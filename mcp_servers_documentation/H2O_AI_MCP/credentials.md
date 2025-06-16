# H2O.ai MCP Server Credentials

## Overview
This document provides instructions on obtaining and structuring the credentials needed to connect the H2O.ai MCP Server in the Vanij Platform.

---

## Credential Format
```json
{
  "H2O_AI": {
    "cluster_url": "http://localhost:54321",
    "username": "admin",
    "password": "admin",
    "api_version": "3"
  }
}
```

---

## How to Set Up H2O.ai Cluster

### Step 1: Install H2O.ai
**Option A: Direct Installation**
```bash
java -jar h2o.jar
```

**Option B: Docker Installation**
```bash
docker run -p 54321:54321 h2oai/h2o-open-source-k8s
```

### Step 2: Access H2O Flow
1. Open browser to `http://localhost:54321`
2. H2O Flow interface will load
3. Default credentials are typically `admin/admin`

### Step 3: Configure Authentication
1. In H2O Flow, go to Admin → Security
2. Set up custom username/password if needed
3. Note the cluster URL and port

---

## Cluster Configuration Options
- **Local**: `http://localhost:54321`
- **Remote**: `http://your-h2o-server:54321`
- **Cloud**: Cloud provider specific URLs
- **Kubernetes**: Service endpoint URLs

---

## Required Setup
- Java 8+ installed for local H2O
- Sufficient memory allocation (4GB+ recommended)
- Network access to H2O cluster
- Port 54321 available (default)

---

## Security Best Practices
- Change default admin credentials
- Use HTTPS in production environments
- Restrict network access to H2O cluster
- Monitor cluster resource usage
