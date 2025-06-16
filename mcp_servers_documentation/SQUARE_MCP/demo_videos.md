# Square MCP Server – Demos and Payload Examples

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
  "SQUARE": {
    "access_token": "EAAAEOuLWr6bASc_your_square_access_token_here",
    "application_id": "sq0idp-your_application_id_here",
    "environment": "sandbox"
  }
}
```

---

## 🧪 API Testing Examples

### Enhanced Sales Summary Tool
```json
{
  "name": "get_sales_summary",
  "arguments": {
    "days": 14
  }
}
```

### Top Products Analysis Tool
```json
{
  "name": "get_top_products", 
  "arguments": {
    "limit": 20
  }
}
```

### List Business Locations
```json
{
  "name": "list_locations",
  "arguments": {}
}
```
