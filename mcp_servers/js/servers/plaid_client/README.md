# Plaid MCP Integration - Remote Server Client

[![Status](https://img.shields.io/badge/status-remote_integration-orange.svg)](https://github.com/your-username/adya-mcp-hackathon)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

## Overview

TypeScript client for integrating with Plaid's official MCP remote server. This connects to Plaid's hosted MCP endpoint to provide banking and financial data access to AI assistants. Built for Team 28 (Code Paglus) in the Adya MCP Hackathon.

## Features

- **Remote Integration**: Connects to official Plaid MCP server
- **OAuth Authentication**: Secure token-based authentication
- **Banking Data**: Account information, transactions, balances
- **Real-time Access**: Live financial data from connected banks
- **Error Handling**: Robust error management and retry logic

## Configuration

### config.json
```json
{
  "client": {
    "name": "plaid-mcp-client",
    "version": "1.0.0",
    "description": "Client for Plaid's remote MCP server",
    "team": "Team 28 - Code Paglus"
  },
  "plaid": {
    "remote_server_url": "https://api.dashboard.plaid.com/mcp/sse",
    "environment": "development",
    "timeout_ms": 15000,
    "retry_attempts": 3
  },
  "authentication": {
    "client_id": "REPLACE_WITH_YOUR_PLAID_CLIENT_ID",
    "secret": "REPLACE_WITH_YOUR_PLAID_SECRET",
    "token_type": "Bearer"
  },
  "available_tools": [
    {
      "name": "get_accounts",
      "description": "List connected bank accounts",
      "category": "accounts"
    },
    {
      "name": "get_transactions",
      "description": "Get transaction history",
      "category": "transactions"
    },
    {
      "name": "get_balances", 
      "description": "Get current account balances",
      "category": "balances"
    },
    {
      "name": "get_identity",
      "description": "Get account holder information",
      "category": "identity"
    }
  ]
}
```

## Installation & Setup

1. **Get Plaid Credentials:**
   - Sign up at [Plaid Dashboard](https://dashboard.plaid.com)
   - Get your `client_id` and `secret` 
   - Enable MCP access in your dashboard

2. **Install dependencies:**
   ```bash
   cd mcp_servers/js/plaid_client
   npm install
   ```

3. **Configure credentials:**
   - Edit `config.json` with your Plaid credentials
   - Set environment to "development" or "production"

4. **Test connection:**
   ```bash
   npm run test
   ```

## Remote MCP Server Integration

### Connection Details

**Endpoint:** `https://api.dashboard.plaid.com/mcp/sse`
**Method:** Server-Sent Events (SSE)
**Authentication:** Bearer token using client credentials

### Authentication Flow

```typescript
// Generate access token
const token = Buffer.from(`${client_id}:${secret}`).toString('base64');
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## Available Tools (Remote)

### `get_accounts()`
Retrieves all connected bank accounts.

**Parameters:** None

**Response:**
```json
{
  "accounts": [
    {
      "account_id": "acc_123456789",
      "name": "Checking Account",
      "official_name": "Bank of Example Checking",
      "type": "depository",
      "subtype": "checking",
      "mask": "0000"
    }
  ]
}
```

### `get_transactions(account_id, start_date, end_date)`
Gets transaction history for an account.

**Parameters:**
- `account_id` (string, required): Account identifier
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)

**Response:**
```json
{
  "transactions": [
    {
      "transaction_id": "txn_987654321",
      "account_id": "acc_123456789", 
      "amount": -42.50,
      "date": "2023-12-01",
      "name": "Coffee Shop Purchase",
      "category": ["Food and Drink", "Restaurants"]
    }
  ],
  "total_transactions": 1
}
```

### `get_balances(account_id)`
Gets current balance information for an account.

**Parameters:**
- `account_id` (string, required): Account identifier

**Response:**
```json
{
  "balances": {
    "available": 1250.75,
    "current": 1320.50,
    "limit": null,
    "iso_currency_code": "USD"
  }
}
```

### `get_identity(account_id)`
Retrieves identity information for account holder.

**Parameters:**
- `account_id` (string, required): Account identifier

**Response:**
```json
{
  "identity": {
    "names": ["John Doe"],
    "addresses": [{
      "data": {
        "street": "123 Main St",
        "city": "San Francisco", 
        "region": "CA",
        "postal_code": "94101",
        "country": "US"
      }
    }],
    "phone_numbers": ["+1-555-123-4567"],
    "emails": ["john.doe@example.com"]
  }
}
```

## Testing & Examples

### Test Script

```bash
# Run integration tests
npm run test

# Test specific functionality
npm run test:accounts
npm run test:transactions
npm run test:auth
```

### Example Usage

```typescript
// Connect to Plaid MCP
const client = new PlaidMCPClient(config);
await client.connect();

// Get all accounts
const accounts = await client.callTool('get_accounts');

// Get recent transactions
const transactions = await client.callTool('get_transactions', {
  account_id: 'acc_123456789',
  start_date: '2023-11-01',
  end_date: '2023-12-01'
});
```

## Error Handling

### Common Error Responses

```json
{
  "error_type": "INVALID_CREDENTIALS",
  "error_code": "INVALID_CLIENT_ID",
  "error_message": "provided client_id is invalid",
  "display_message": "Invalid credentials provided"
}
```

### Error Types
- `INVALID_CREDENTIALS`: Authentication failed
- `ITEM_LOGIN_REQUIRED`: User needs to re-authenticate
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `ITEM_NOT_FOUND`: Account/item not found
- `API_ERROR`: General API error

## Rate Limits

- **Development**: 100 requests per minute
- **Production**: 600 requests per minute  
- **Burst**: Up to 10 concurrent requests

## Security Notes

- All communication uses HTTPS/TLS
- Credentials are never logged or stored
- Tokens expire and require refresh
- Sensitive data is encrypted in transit

## Development

### Project Structure
```
plaid_client/
├── src/
│   ├── client.ts         # Main MCP client
│   ├── auth.ts          # Authentication handler
│   ├── types.ts         # TypeScript definitions
│   └── test.ts          # Integration tests
├── config.json          # Configuration
├── package.json
└── README.md           # This file
```

### Adding New Tools

To use additional Plaid MCP tools:
1. Check Plaid's MCP documentation
2. Add tool definition to `config.json`
3. Implement client call in `src/client.ts`
4. Add tests and documentation

Built with ❤️ by Team 28 - Code Paglus
