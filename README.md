# Cloud Cost Optimization – Stale Snapshot Cleanup Automation  

Automated cleanup of **stale EBS snapshots** using **AWS Lambda + Python + boto3**, with **tag-based protection** and **cost estimation**.  
This helps reduce unnecessary storage costs in AWS by identifying snapshots no longer linked to active EC2 volumes.

---

## Features

- **Detect stale EBS snapshots**
- **Tag-based protection (`Keep=true`, `Environment=production`)**
- **Cost estimation per month**
- **CloudWatch logging visibility**
- **boto3 execution with Lambda**

---

## Architecture Flow
```
AWS Lambda (boto3)
│
├─ DescribeSnapshots()
├─ DescribeInstances()
│
├─ Identify stale snapshots (no active volume)
├─ Apply safety tags rules
└─ Estimate cost & delete (if DRY_RUN=false)
```
## Project Details

**Tech Used**  
`AWS Lambda` · `Python` · `boto3` · `CloudWatch`

**Core Highlights**
- Automated stale snapshot detection & cleanup to reduce cloud storage cost  
- Tag-based safety (`Keep=true`, `Environment=production`) prevents accidental removal  
- Estimated total snapshot size & monthly cost savings via CloudWatch logs  

---

## How to Use

1. Create IAM role with Snapshot read/delete permissions  
2. Deploy code in AWS Lambda (Python runtime)  
3. Set Environment Variable `DRY_RUN=true` to test  
4. Set `DRY_RUN=false` to enable real deletion  
5. Monitor execution in CloudWatch Logs  

---


