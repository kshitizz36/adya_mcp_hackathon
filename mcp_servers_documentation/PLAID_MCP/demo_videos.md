# Plaid MCP Server – Demos and Payload Examples

## 🎥 Demo Video
- **MCP server setup explanation + API Execution + Features Testing**: [Watch Here](https://your-demo-video-link.com)

---

## 🎥 Credentials Gathering Video
- **Gathering Credentials & Setup(Full end-to-end video)**: [Watch Here](https://your-demo-video-link.com)

---

## 🔐 Credential JSON Payload
Example payload format for sending credentials to the MCP Server which going to be use it in Client API payload:
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

## 🧪 API Testing Examples

### Get Connected Accounts
```json
{
  "name": "get_accounts",
  "arguments": {}
}
```

### Get Transaction History
```json
{
  "name": "get_transactions",
  "arguments": {
    "account_id": "acc_123456789",
    "start_date": "2023-11-01",
    "end_date": "2023-12-01",
    "count": 50
  }
}
```

### Get Account Balances
```json
{
  "name": "get_balances",
  "arguments": {
    "account_id": "acc_123456789"
  }
}
```

### Get Identity Information
```json
{
  "name": "get_identity",
  "arguments": {
    "account_id": "acc_123456789"
  }
}
```

### Get Liabilities
```json
{
  "name": "get_liabilities",
  "arguments": {
    "account_id": "acc_123456789"
  }
}
```
