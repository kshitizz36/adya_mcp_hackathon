# Square MCP Server - Enhanced

[![Status](https://img.shields.io/badge/status-enhanced-green.svg)](https://github.com/your-username/adya-mcp-hackathon)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

## Overview

Enhanced Square MCP server that extends the official Square MCP with custom analytics and reporting tools. Built for Team 28 (Code Paglus) in the Adya MCP Hackathon.

## Features

- **Standard Square Tools**: Location management, order retrieval
- **Enhanced Analytics**: Custom sales summaries and product performance reports  
- **Real-time Data**: Live connection to Square API
- **Production Ready**: Error handling, logging, and proper authentication

## Configuration

### config.json
```json
{
  "server": {
    "name": "square-mcp-enhanced",
    "version": "1.0.0",
    "port": 3001,
    "description": "Enhanced Square MCP with custom analytics tools"
  },
  "square": {
    "environment": "sandbox",
    "api_version": "2023-10-18",
    "base_url": {
      "sandbox": "https://connect.squareupsandbox.com/v2",
      "production": "https://connect.squareup.com/v2"
    }
  },
  "credentials": {
    "access_token": "YOUR_SQUARE_ACCESS_TOKEN_HERE",
    "application_id": "YOUR_SQUARE_APPLICATION_ID_HERE"
  },
  "tools": [
    {
      "name": "list_locations",
      "type": "standard",
      "description": "List all business locations"
    },
    {
      "name": "get_sales_summary", 
      "type": "enhanced",
      "description": "Generate sales summary report",
      "default_days": 7
    },
    {
      "name": "get_top_products",
      "type": "enhanced", 
      "description": "Get best-selling products",
      "default_limit": 10
    },
    {
      "name": "list_orders",
      "type": "standard",
      "description": "List orders for a location"
    }
  ]
}
```

## Installation & Setup

1. **Install dependencies:**
   ```bash
   cd mcp_servers/js/square_mcp
   npm install
   ```

2. **Configure credentials:**
   - Copy `config.example.json` to `config.json`  
   - Add your Square access token and application ID
   - Set environment to "sandbox" or "production"

3. **Start the server:**
   ```bash
   npm run dev
   ```

## API Tools Documentation

### Standard Tools (from Square MCP)

#### `list_locations()`
Lists all business locations associated with your Square account.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "location_id",
      "name": "Main Store",
      "address": {...},
      "status": "ACTIVE"
    }
  ]
}
```

#### `list_orders(location_id)`
Lists orders for a specific location.

**Parameters:**
- `location_id` (string, required): The location ID

**Response:**
```json
{
  "success": true, 
  "data": [
    {
      "id": "order_id",
      "total_money": {"amount": 1500, "currency": "USD"},
      "created_at": "2023-12-01T10:30:00Z"
    }
  ]
}
```

### Enhanced Tools (Custom)

#### `get_sales_summary(days?)`
Generates comprehensive sales analytics for specified time period.

**Parameters:**
- `days` (number, optional): Number of days to analyze (default: 7)

**Response:**
```json
{
  "success": true,
  "data": {
    "period_days": 7,
    "total_sales_cents": 150000,
    "total_sales_dollars": 1500.00,
    "transaction_count": 45,
    "average_order_value_cents": 3333,
    "average_order_value_dollars": 33.33,
    "date_range": {
      "start": "2023-11-24",
      "end": "2023-12-01"
    }
  }
}
```

#### `get_top_products(limit?)`
Returns best-performing products with sales metrics.

**Parameters:**
- `limit` (number, optional): Maximum products to return (default: 10)

**Response:**
```json
{
  "success": true,
  "data": {
    "top_products": [
      {
        "id": "item_id",
        "name": "Coffee Latte",
        "category": "Beverages",
        "simulated_units_sold": 87,
        "simulated_revenue_cents": 8700,
        "rank": 1
      }
    ],
    "total_items_analyzed": 25,
    "limit_applied": 10
  }
}
```

## Testing

```bash
# Test connection
curl http://localhost:3001/health

# List available tools
curl http://localhost:3001/mcp/tools

# Test sales summary
curl -X POST http://localhost:3001/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "get_sales_summary", "arguments": {"days": 14}}'
```

## Error Handling

All tools return standardized error responses:

```json
{
  "success": false,
  "error": "Error description here"
}
```

Common errors:
- Invalid Square credentials
- Network connectivity issues  
- Invalid location IDs
- Rate limiting (429 status)

## Development

### Project Structure
```
square_mcp/
├── src/
│   ├── index.ts          # Main server
│   ├── config.json       # Configuration
│   └── types.ts          # TypeScript definitions
├── package.json
└── README.md            # This file
```

### Adding Custom Tools

1. Define tool in `config.json`
2. Add implementation in `src/index.ts`
3. Update documentation
4. Test thoroughly

Built with ❤️ by Team 28 - Code Paglus
