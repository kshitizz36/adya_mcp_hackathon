# GitHub MCP Server Credentials

## Overview
This document provides instructions on obtaining and structuring the credentials needed to connect the GitHub MCP Server in the Vanij Platform.

---

## Credential Format
```json
{
  "GITHUB": {
    "token": "ghp_your_github_personal_access_token_here",
    "username": "your-github-username"
  }
}
```

---

## How to Obtain GitHub Personal Access Token

### Step 1: Access GitHub Settings
1. Log in to GitHub
2. Click your profile picture → Settings
3. Navigate to "Developer settings" (bottom left)
4. Click "Personal access tokens" → "Tokens (classic)"

### Step 2: Generate New Token
1. Click "Generate new token (classic)"
2. Add a descriptive note (e.g., "MCP Server Access")
3. Set expiration (recommended: 90 days)

### Step 3: Select Scopes
Required permissions:
- ✅ `repo` - Full repository access
- ✅ `read:user` - Read user profile data
- ✅ `read:org` - Read organization data
- ✅ `write:repo_hook` - Write repository hooks (if needed)

### Step 4: Generate and Copy Token
1. Click "Generate token"
2. **Copy the token immediately** (you won't see it again)
3. Store securely in your credential management system

---

## Token Security Best Practices
- Never commit tokens to version control
- Use environment variables or secure storage
- Set appropriate expiration dates
- Rotate tokens regularly
- Use minimal required scopes

---

## Rate Limits
- **Authenticated**: 5,000 requests per hour
- **Unauthenticated**: 60 requests per hour
- **Search API**: 30 requests per minute
- **Abuse detection**: Automatic rate limiting
