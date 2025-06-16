# Plaid MCP Server Credentials

## Overview
This document provides instructions on obtaining and structuring the credentials needed to connect the Plaid MCP Server in the Vanij Platform.

---

## Credential Format
```json
{
  "PLAID": {
    "client_id": "your_plaid_client_id_here",
    "secret": "your_plaid_secret_here",
    "environment": "development",
    "remote_server_url": "https://api.dashboard.plaid.com/mcp/sse"
  }
}
```

---

## How to Obtain Plaid Credentials

### Step 1: Create Plaid Account
1. Visit [Plaid Dashboard](https://dashboard.plaid.com)
2. Sign up for a new account
3. Complete the verification process

### Step 2: Create Application
1. In the dashboard, click "Create Application"
2. Choose application type (Personal Finance, Lending, etc.)
3. Select required products (Transactions, Auth, Identity, etc.)
4. Provide application details

### Step 3: Get API Keys
1. Navigate to "API" section in your app dashboard
2. Copy your **Client ID**
3. Copy your **Secret key**
4. Note the environment (development/production)

### Step 4: Enable MCP Access
1. In your Plaid dashboard, go to Settings
2. Enable "Model Context Protocol" access
3. Whitelist your application for MCP usage

---

## Environment Configuration
- **Development**: For testing with fake bank data
- **Production**: For live banking connections
- **Sandbox**: For development with simulated data

---

## Required Plaid Products
- **Transactions**: Access to transaction history
- **Auth**: Account and routing number verification
- **Identity**: Account holder information
- **Assets**: Account balance and asset information

---

## Security Best Practices
- Keep secret keys secure and never expose in client code
- Use HTTPS for all API communications
- Implement proper error handling for failed connections
- Monitor API usage and rate limits
