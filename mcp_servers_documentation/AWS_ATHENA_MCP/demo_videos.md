# AWS Athena MCP Server – Demos and Payload Examples

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

## 🧪 API Testing Examples

### Execute SQL Query
```json
{
  "name": "execute_query",
  "arguments": {
    "sql": "SELECT * FROM my_table LIMIT 10",
    "database": "analytics"
  }
}
```

### List Available Databases
```json
{
  "name": "list_databases",
  "arguments": {}
}
```

### List Tables in Database
```json
{
  "name": "list_tables",
  "arguments": {
    "database": "analytics"
  }
}
```

### Get Query Execution Status
```json
{
  "name": "get_query_execution",
  "arguments": {
    "query_id": "12345678-1234-1234-1234-123456789012"
  }
}
```

### Cancel Running Query
```json
{
  "name": "cancel_query",
  "arguments": {
    "query_id": "12345678-1234-1234-1234-123456789012"
  }
}
```
