# H2O.ai MCP Server - Built from Scratch

[![Status](https://img.shields.io/badge/status-custom_build-blue.svg)](https://github.com/your-username/adya-mcp-hackathon)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

## Overview

Custom-built H2O.ai MCP server that provides AI assistants with direct access to H2O.ai machine learning clusters. No official MCP exists for H2O.ai, so this was built from scratch for Team 28 (Code Paglus) in the Adya MCP Hackathon.

## Features

- **Cluster Management**: Connect and monitor H2O.ai clusters
- **Model Operations**: List, inspect, and manage ML models  
- **Data Frame Access**: Browse and analyze data frames
- **Real-time Status**: Live cluster health and performance monitoring
- **Auto-Discovery**: Automatic model and frame detection

## Configuration

### config.json
```json
{
  "server": {
    "name": "h2o-ai-mcp-server",
    "version": "1.0.0", 
    "port": 3002,
    "description": "Custom H2O.ai MCP for ML operations"
  },
  "h2o": {
    "default_cluster_url": "http://localhost:54321",
    "connection_timeout_ms": 10000,
    "api_version": "3",
    "auto_connect": true
  },
  "authentication": {
    "username": "admin",
    "password": "admin",
    "method": "basic"
  },
  "tools": [
    {
      "name": "connect_to_cluster",
      "description": "Connect to H2O.ai cluster",
      "category": "connection"
    },
    {
      "name": "list_models", 
      "description": "List all ML models",
      "category": "models"
    },
    {
      "name": "list_frames",
      "description": "List all data frames", 
      "category": "data"
    },
    {
      "name": "get_model_details",
      "description": "Get detailed model information",
      "category": "models"
    },
    {
      "name": "get_cluster_status",
      "description": "Get cluster health and metrics",
      "category": "monitoring"
    }
  ]
}
```

## Installation & Setup

1. **Install H2O.ai:**
   ```bash
   # Download and start H2O
   java -jar h2o.jar
   # Or use Docker
   docker run -p 54321:54321 h2oai/h2o-open-source-k8s
   ```

2. **Install MCP server:**
   ```bash
   cd mcp_servers/js/h2o_ai_mcp
   npm install
   ```

3. **Configure connection:**
   - Edit `config.json` with your H2O cluster URL
   - Set authentication credentials if required
   - Adjust timeout and connection settings

4. **Start the server:**
   ```bash
   npm run dev
   ```

## API Tools Documentation

### Connection Tools

#### `connect_to_cluster(url?)`
Establishes connection to H2O.ai cluster.

**Parameters:**
- `url` (string, optional): Cluster URL (uses config default if not provided)

**Response:**
```json
{
  "success": true,
  "data": {
    "connected": true,
    "cluster_url": "http://localhost:54321",
    "cluster_info": {
      "version": "3.42.0.3",
      "build_number": "3.42.0.3",
      "nodes": 1,
      "status": "Connected"
    }
  }
}
```

### Model Management Tools

#### `list_models()`
Lists all available machine learning models in the cluster.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model_id": "GBM_model_1701234567890",
        "algorithm": "gbm",
        "training_frame": "train_data.hex",
        "status": "DONE",
        "creation_time": 1701234567890
      }
    ],
    "total_count": 5
  }
}
```

#### `get_model_details(model_id)`
Retrieves comprehensive information about a specific model.

**Parameters:**
- `model_id` (string, required): The model identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "model_id": "GBM_model_1701234567890",
    "algorithm": "gbm",
    "parameters": {
      "ntrees": 50,
      "max_depth": 6,
      "learn_rate": 0.1
    },
    "metrics": {
      "mse": 0.0234,
      "rmse": 0.1529,
      "mae": 0.1123,
      "rmsle": 0.0987
    },
    "training_frame": "train_data.hex",
    "validation_frame": "valid_data.hex",
    "status": "DONE",
    "training_time_ms": 12567
  }
}
```

### Data Management Tools

#### `list_frames()`
Lists all data frames available in the cluster.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "data": {
    "frames": [
      {
        "frame_id": "train_data.hex",
        "rows": 10000,
        "columns": 25, 
        "size_bytes": 2048576,
        "checksum": "3456789012"
      }
    ],
    "total_count": 3
  }
}
```

### Monitoring Tools

#### `get_cluster_status()`
Provides real-time cluster health and performance metrics.

**Parameters:** None

**Response:**
```json
{
  "success": true,
  "data": {
    "cluster_healthy": true,
    "version": "3.42.0.3",
    "uptime_ms": 3600000,
    "nodes": [
      {
        "name": "node1",
        "ip_port": "127.0.0.1:54321",
        "healthy": true,
        "last_ping": 1701234567890,
        "memory_usage": {
          "free": 2147483648,
          "total": 4294967296,
          "used_percent": 50
        }
      }
    ],
    "recent_activity": [
      {
        "timestamp": 1701234567890,
        "event": "Model training completed",
        "details": "GBM_model_1701234567890"
      }
    ]
  }
}
```

## Testing

```bash
# Test server health
curl http://localhost:3002/health

# Test cluster connection  
curl -X POST http://localhost:3002/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "connect_to_cluster"}'

# List models
curl -X POST http://localhost:3002/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "list_models"}'
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure H2O.ai is running on specified port
   - Check firewall settings
   - Verify authentication credentials

2. **No Models Found**
   - Import data and train models in H2O Flow
   - Check cluster is properly initialized

3. **Timeout Errors**
   - Increase `connection_timeout_ms` in config
   - Check network latency to H2O cluster

### Error Responses

```json
{
  "success": false, 
  "error": "Failed to connect to H2O cluster: Connection refused"
}
```

## Development

### Project Structure
```
h2o_ai_mcp/
├── src/
│   ├── index.ts          # Main server
│   ├── h2o-client.ts     # H2O API wrapper  
│   └── types.ts          # TypeScript definitions
├── config.json           # Configuration
├── package.json
└── README.md            # This file
```

### Extending Functionality

Add new tools by:
1. Defining tool schema in `config.json`
2. Implementing handler in `src/index.ts`
3. Adding H2O API calls in `src/h2o-client.ts`
4. Updating documentation

Built with ❤️ by Team 28 - Code Paglus
