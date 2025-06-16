# GitHub MCP Server – Demos and Payload Examples

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
  "GITHUB": {
    "token": "ghp_your_github_personal_access_token_here",
    "username": "your-github-username"
  }
}
```

---

## 🧪 API Testing Examples

### Get Repository Details
```json
{
  "name": "get_repo_details",
  "arguments": {
    "owner": "microsoft",
    "repo": "vscode"
  }
}
```

### List Repository Issues
```json
{
  "name": "list_issues",
  "arguments": {
    "owner": "facebook",
    "repo": "react",
    "state": "open",
    "limit": 10
  }
}
```

### Create New Issue
```json
{
  "name": "create_issue",
  "arguments": {
    "owner": "your-username",
    "repo": "your-repo",
    "title": "Bug: Login not working",
    "body": "Detailed description of the issue...",
    "labels": ["bug", "urgent"]
  }
}
```

### Search Repositories  
```json
{
  "name": "search_repositories",
  "arguments": {
    "query": "machine learning python",
    "sort": "stars",
    "limit": 15
  }
}
```

### List Pull Requests
```json
{
  "name": "list_pull_requests",
  "arguments": {
    "owner": "vercel",
    "repo": "next.js",
    "state": "open"
  }
}
```
