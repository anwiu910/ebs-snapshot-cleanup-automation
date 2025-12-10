import boto3
import os

ec2 = boto3.client("ec2")

SNAPSHOT_PRICE = float(os.getenv("SNAPSHOT_PRICE", "0.05"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def get_all_snapshots():
    paginator = ec2.get_paginator("describe_snapshots")
    for page in paginator.paginate(OwnerIds=["self"]):
        for snap in page["Snapshots"]:
            yield snap


def get_active_volumes():
    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]
    )
    active_volumes = set()
    for page in pages:
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                for blk in instance.get("BlockDeviceMappings", []):
                    if "Ebs" in blk:
                        active_volumes.add(blk["Ebs"]["VolumeId"])
    return active_volumes


def lambda_handler(event, context):
    active_volumes = get_active_volumes()
    stale_snapshots = []
    total_size_gb = 0

    for snap in get_all_snapshots():
        snap_id = snap["SnapshotId"]
        size = snap["VolumeSize"]
        tags = {t["Key"]: t["Value"] for t in snap.get("Tags", [])}

        # Tag-based protection
        if tags.get("Keep", "").lower() == "true":
            print(f"Skipping snapshot {snap_id} (tag Keep=true)")
            continue
        if tags.get("Environment", "").lower() == "production":
            print(f"Skipping snapshot {snap_id} (Production environment)")
            continue

        volume_id = snap.get("VolumeId")

        if not volume_id:
            print(f"Snapshot {snap_id} has no VolumeId, marking as stale")
            stale_snapshots.append(snap_id)
            total_size_gb += size
            continue

        if volume_id not in active_volumes:
            print(
                f"Snapshot {snap_id} is not linked to an active volume ({volume_id}), "
                "marking as stale"
            )
            stale_snapshots.append(snap_id)
            total_size_gb += size
        else:
            print(f"Snapshot {snap_id} still belongs to active volume {volume_id}")

    estimated_saving = total_size_gb * SNAPSHOT_PRICE

    print(
        f"Found {len(stale_snapshots)} stale snapshots "
        f"({total_size_gb} GB). Estimated saving: ${estimated_saving:.2f}/month"
    )
    print(f"DRY_RUN = {DRY_RUN} (no deletion if True)")

    if not DRY_RUN:
        for snap_id in stale_snapshots:
            try:
                print(f"Deleting stale snapshot: {snap_id}")
                ec2.delete_snapshot(SnapshotId=snap_id)
            except Exception as e:
                print(f"Failed to delete snapshot {snap_id}: {str(e)}")
    else:
        for snap_id in stale_snapshots:
            print(f"[DRY-RUN] Would delete stale snapshot: {snap_id}")

    return {
        "deleted_snapshots": stale_snapshots if not DRY_RUN else [],
        "stale_snapshots_detected": stale_snapshots,
        "count": len(stale_snapshots),
        "total_gb": total_size_gb,
        "estimated_monthly_saving": estimated_saving,
        "dry_run": DRY_RUN,
    }
