# H2O.ai MCP Server – Demos and Payload Examples

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
  "H2O_AI": {
    "cluster_url": "http://localhost:54321",
    "username": "admin",
    "password": "admin",
    "api_version": "3"
  }
}
```

---

## 🧪 API Testing Examples

### Connect to H2O Cluster
```json
{
  "name": "connect_to_cluster",
  "arguments": {
    "url": "http://localhost:54321"
  }
}
```

### List All ML Models
```json
{
  "name": "list_models",
  "arguments": {}
}
```

### Get Model Details
```json
{
  "name": "get_model_details",
  "arguments": {
    "model_id": "GBM_model_1701234567890"
  }
}
```

### List Data Frames
```json
{
  "name": "list_frames",
  "arguments": {}
}
```

### Get Cluster Status
```json
{
  "name": "get_cluster_status",
  "arguments": {}
}
```
