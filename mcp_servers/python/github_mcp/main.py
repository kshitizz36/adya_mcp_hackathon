#!/usr/bin/env python3
"""
GitHub MCP Server - Python Implementation
Following MCP Protocol Standards for repository and issue management
Team 28 - Code Paglus - Adya MCP Hackathon
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("github-mcp")

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Configuration loaded successfully")
except FileNotFoundError:
    logger.error("config.json not found. Please create configuration file.")
    config = {}

# Initialize MCP server
server = Server("github-mcp")

# GitHub API configuration
GITHUB_BASE_URL = "https://api.github.com"
GITHUB_HEADERS = {
    "Authorization": f"token {config.get('authentication', {}).get('token', '')}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Team28-GitHub-MCP/1.0.0"
}

async def make_github_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
    """Make authenticated request to GitHub API"""
    url = f"{GITHUB_BASE_URL}{endpoint}"
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method, 
                url, 
                headers=GITHUB_HEADERS, 
                json=data,
                params=params
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    error_msg = f"GitHub API Error ({response.status}): {error_data.get('message', 'Unknown error')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return await response.json()
    except aiohttp.ClientError as e:
        error_msg = f"Network error calling GitHub API: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error calling GitHub API: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools following MCP protocol"""
    return [
        Tool(
            name="get_repo_details",
            description="Get comprehensive information about a GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        Tool(
            name="list_issues",
            description="List issues for a repository with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "state": {
                        "type": "string",
                        "description": "Issue state",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to return",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        Tool(
            name="create_issue",
            description="Create a new issue in a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue description/body"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of label names"
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of usernames to assign"
                    }
                },
                "required": ["owner", "repo", "title"]
            }
        ),
        Tool(
            name="search_repositories",
            description="Search GitHub repositories with advanced filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort criteria",
                        "enum": ["stars", "forks", "help-wanted-issues", "updated"],
                        "default": "stars"
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order",
                        "enum": ["asc", "desc"],
                        "default": "desc"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_user_profile",
            description="Get detailed information about a GitHub user",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub username"
                    }
                },
                "required": ["username"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution following MCP protocol"""
    
    try:
        if name == "get_repo_details":
            return await get_repo_details(arguments.get("owner"), arguments.get("repo"))
        elif name == "list_issues":
            return await list_issues(
                arguments.get("owner"), 
                arguments.get("repo"),
                arguments.get("state", "open"),
                arguments.get("limit", 30)
            )
        elif name == "create_issue":
            return await create_issue(
                arguments.get("owner"),
                arguments.get("repo"),
                arguments.get("title"),
                arguments.get("body", ""),
                arguments.get("labels"),
                arguments.get("assignees")
            )
        elif name == "search_repositories":
            return await search_repositories(
                arguments.get("query"),
                arguments.get("sort", "stars"),
                arguments.get("order", "desc"),
                arguments.get("limit", 10)
            )
        elif name == "get_user_profile":
            return await get_user_profile(arguments.get("username"))
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "tool": name,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]

async def get_repo_details(owner: str, repo: str) -> List[types.TextContent]:
    """Get comprehensive repository information"""
    try:
        logger.info(f"Getting details for repository {owner}/{repo}")
        
        # Get basic repo info
        repo_data = await make_github_request(f"/repos/{owner}/{repo}")
        
        # Get additional stats
        try:
            contributors = await make_github_request(f"/repos/{owner}/{repo}/contributors", params={"per_page": 5})
            languages = await make_github_request(f"/repos/{owner}/{repo}/languages")
            releases = await make_github_request(f"/repos/{owner}/{repo}/releases", params={"per_page": 3})
        except:
            contributors = []
            languages = {}
            releases = []
        
        response_data = {
            "success": True,
            "repository": {
                "basic_info": {
                    "id": repo_data["id"],
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data["description"],
                    "private": repo_data["private"],
                    "fork": repo_data["fork"],
                    "archived": repo_data["archived"],
                    "disabled": repo_data["disabled"]
                },
                "urls": {
                    "html_url": repo_data["html_url"],
                    "clone_url": repo_data["clone_url"],
                    "ssh_url": repo_data["ssh_url"],
                    "homepage": repo_data["homepage"]
                },
                "statistics": {
                    "stars": repo_data["stargazers_count"],
                    "watchers": repo_data["watchers_count"],
                    "forks": repo_data["forks_count"],
                    "open_issues": repo_data["open_issues_count"],
                    "size_kb": repo_data["size"],
                    "network_count": repo_data["network_count"],
                    "subscribers_count": repo_data["subscribers_count"]
                },
                "details": {
                    "language": repo_data["language"],
                    "languages": languages,
                    "default_branch": repo_data["default_branch"],
                    "topics": repo_data.get("topics", []),
                    "license": repo_data["license"]["name"] if repo_data.get("license") else None,
                    "has_issues": repo_data["has_issues"],
                    "has_projects": repo_data["has_projects"],
                    "has_wiki": repo_data["has_wiki"],
                    "has_pages": repo_data["has_pages"]
                },
                "timestamps": {
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "pushed_at": repo_data["pushed_at"]
                },
                "owner": {
                    "login": repo_data["owner"]["login"],
                    "type": repo_data["owner"]["type"],
                    "avatar_url": repo_data["owner"]["avatar_url"]
                },
                "top_contributors": [
                    {
                        "login": contrib["login"],
                        "contributions": contrib["contributions"],
                        "avatar_url": contrib["avatar_url"]
                    } for contrib in contributors[:5]
                ],
                "recent_releases": [
                    {
                        "tag_name": release["tag_name"],
                        "name": release["name"],
                        "published_at": release["published_at"],
                        "prerelease": release["prerelease"]
                    } for release in releases[:3]
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "repository": f"{owner}/{repo}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def list_issues(owner: str, repo: str, state: str = "open", limit: int = 30) -> List[types.TextContent]:
    """List repository issues with filtering"""
    try:
        logger.info(f"Listing issues for {owner}/{repo} with state {state}")
        
        params = {"state": state, "per_page": min(limit, 100)}
        issues_data = await make_github_request(f"/repos/{owner}/{repo}/issues", params=params)
        
        processed_issues = []
        label_counts = {}
        assignee_counts = {}
        
        for issue in issues_data:
            # Skip pull requests (they appear in issues API)
            if issue.get("pull_request"):
                continue
                
            # Count labels and assignees
            for label in issue.get("labels", []):
                label_name = label["name"]
                label_counts[label_name] = label_counts.get(label_name, 0) + 1
            
            for assignee in issue.get("assignees", []):
                assignee_name = assignee["login"]
                assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
            
            processed_issues.append({
                "id": issue["id"],
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"][:500] + "..." if issue.get("body") and len(issue["body"]) > 500 else issue.get("body", ""),
                "state": issue["state"],
                "locked": issue["locked"],
                "user": {
                    "login": issue["user"]["login"],
                    "avatar_url": issue["user"]["avatar_url"]
                },
                "labels": [
                    {
                        "name": label["name"],
                        "color": label["color"],
                        "description": label.get("description")
                    } for label in issue["labels"]
                ],
                "assignees": [assignee["login"] for assignee in issue["assignees"]],
                "milestone": {
                    "title": issue["milestone"]["title"],
                    "number": issue["milestone"]["number"]
                } if issue.get("milestone") else None,
                "comments": issue["comments"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "closed_at": issue["closed_at"],
                "html_url": issue["html_url"]
            })
        
        response_data = {
            "success": True,
            "issues": processed_issues,
            "repository": f"{owner}/{repo}",
            "filters": {
                "state": state,
                "limit": limit
            },
            "summary": {
                "total_returned": len(processed_issues),
                "most_common_labels": sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "most_assigned_users": sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "repository": f"{owner}/{repo}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def create_issue(owner: str, repo: str, title: str, body: str = "", labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> List[types.TextContent]:
    """Create a new issue in repository"""
    try:
        logger.info(f"Creating issue in {owner}/{repo}: {title}")
        
        issue_data = {
            "title": title,
            "body": body
        }
        
        if labels:
            issue_data["labels"] = labels
        
        if assignees:
            issue_data["assignees"] = assignees
        
        result = await make_github_request(f"/repos/{owner}/{repo}/issues", "POST", issue_data)
        
        response_data = {
            "success": True,
            "created_issue": {
                "id": result["id"],
                "number": result["number"],
                "title": result["title"],
                "body": result["body"],
                "state": result["state"],
                "user": {
                    "login": result["user"]["login"],
                    "avatar_url": result["user"]["avatar_url"]
                },
                "labels": [label["name"] for label in result["labels"]],
                "assignees": [assignee["login"] for assignee in result["assignees"]],
                "html_url": result["html_url"],
                "created_at": result["created_at"]
            },
            "repository": f"{owner}/{repo}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "repository": f"{owner}/{repo}",
            "attempted_title": title,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def search_repositories(query: str, sort: str = "stars", order: str = "desc", limit: int = 10) -> List[types.TextContent]:
    """Search GitHub repositories"""
    try:
        logger.info(f"Searching repositories: {query}")
        
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(limit, 100)
        }
        
        result = await make_github_request("/search/repositories", params=params)
        
        processed_repos = []
        language_stats = {}
        
        for repo in result["items"]:
            language = repo.get("language", "Unknown")
            language_stats[language] = language_stats.get(language, 0) + 1
            
            processed_repos.append({
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "html_url": repo["html_url"],
                "language": language,
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "open_issues": repo["open_issues_count"],
                "size_kb": repo["size"],
                "owner": {
                    "login": repo["owner"]["login"],
                    "type": repo["owner"]["type"],
                    "avatar_url": repo["owner"]["avatar_url"]
                },
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "pushed_at": repo["pushed_at"],
                "topics": repo.get("topics", []),
                "license": repo["license"]["name"] if repo.get("license") else None,
                "archived": repo["archived"],
                "fork": repo["fork"]
            })
        
        response_data = {
            "success": True,
            "search_results": {
                "query": query,
                "total_count": result["total_count"],
                "incomplete_results": result["incomplete_results"],
                "repositories": processed_repos
            },
            "search_parameters": {
                "sort": sort,
                "order": order,
                "limit": limit
            },
            "statistics": {
                "returned_count": len(processed_repos),
                "language_distribution": sorted(language_stats.items(), key=lambda x: x[1], reverse=True),
                "total_stars": sum(repo["stars"] for repo in processed_repos),
                "total_forks": sum(repo["forks"] for repo in processed_repos)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "search_query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_user_profile(username: str) -> List[types.TextContent]:
    """Get detailed user profile information"""
    try:
        logger.info(f"Getting profile for user {username}")
        
        # Get user profile
        user_data = await make_github_request(f"/users/{username}")
        
        # Get user's repositories (top 10)
        try:
            repos = await make_github_request(f"/users/{username}/repos", params={"per_page": 10, "sort": "updated"})
        except:
            repos = []
        
        # Get user's organizations
        try:
            orgs = await make_github_request(f"/users/{username}/orgs")
        except:
            orgs = []
        
        response_data = {
            "success": True,
            "user_profile": {
                "basic_info": {
                    "id": user_data["id"],
                    "login": user_data["login"],
                    "name": user_data["name"],
                    "bio": user_data["bio"],
                    "avatar_url": user_data["avatar_url"],
                    "html_url": user_data["html_url"],
                    "type": user_data["type"],
                    "site_admin": user_data["site_admin"]
                },
                "contact": {
                    "email": user_data["email"],
                    "blog": user_data["blog"],
                    "twitter_username": user_data["twitter_username"],
                    "location": user_data["location"],
                    "company": user_data["company"]
                },
                "statistics": {
                    "public_repos": user_data["public_repos"],
                    "public_gists": user_data["public_gists"],
                    "followers": user_data["followers"],
                    "following": user_data["following"]
                },
                "timestamps": {
                    "created_at": user_data["created_at"],
                    "updated_at": user_data["updated_at"]
                },
                "recent_repositories": [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo["description"],
                        "language": repo["language"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "updated_at": repo["updated_at"],
                        "html_url": repo["html_url"]
                    } for repo in repos[:10]
                ],
                "organizations": [
                    {
                        "login": org["login"],
                        "description": org.get("description"),
                        "avatar_url": org["avatar_url"]
                    } for org in orgs
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": str(e),
            "username": username,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def main():
    """Run the MCP server using stdin/stdout streams"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="github-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
