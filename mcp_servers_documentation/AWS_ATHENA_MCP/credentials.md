# AWS Athena MCP Server Credentials

## Overview
This document provides instructions on obtaining and structuring the credentials needed to connect the AWS Athena MCP Server in the Vanij Platform.

---

## Credential Format
```json
{
  "AWS_ATHENA": {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "region": "us-east-1",
    "database": "default",
    "workgroup": "primary"
  }
}
```

---

## How to Obtain AWS Credentials

### Step 1: Create AWS Account
1. Visit [AWS Console](https://aws.amazon.com)
2. Sign up or log in to your AWS account
3. Navigate to IAM (Identity and Access Management)

### Step 2: Create IAM User
1. Go to IAM → Users → Add User
2. Enter username (e.g., "athena-mcp-user")
3. Select "Programmatic access"
4. Click "Next: Permissions"

### Step 3: Attach Policies
Required permissions:
- ✅ `AmazonAthenaFullAccess`
- ✅ `AmazonS3ReadOnlyAccess` (for data access)
- ✅ `AWSGlueConsoleFullAccess` (for data catalog)

### Step 4: Get Access Keys
1. Complete user creation
2. **Download CSV with credentials** or copy:
   - Access Key ID
   - Secret Access Key
3. Store credentials securely

---

## Athena Setup Requirements

### Step 1: Configure S3 Bucket
1. Create S3 bucket for query results
2. Set appropriate permissions
3. Note bucket name and region

### Step 2: Set Up Data Sources
1. Create databases in AWS Glue Data Catalog
2. Add tables pointing to S3 data
3. Configure table schemas and partitions

### Step 3: Configure Workgroup
1. Go to Athena console
2. Create or configure workgroup
3. Set query result location to your S3 bucket

---

## Security Best Practices
- Use IAM roles instead of access keys when possible
- Implement least privilege access policies
- Enable CloudTrail for API logging
- Rotate access keys regularly
- Use VPC endpoints for private connectivity
