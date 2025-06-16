import express from 'express';
import cors from 'cors';
import axios from 'axios';
import fs from 'fs';
import path from 'path';

const app = express();
app.use(cors());
app.use(express.json());

// Load configuration
const configPath = path.join(__dirname, '../config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const PORT = config.server.port;
const GITHUB_BASE_URL = 'https://api.github.com';

// GitHub headers with token from config
const getGithubHeaders = () => ({
  'Authorization': `token ${config.authentication.token}`,
  'Accept': 'application/vnd.github.v3+json',
  'User-Agent': 'GitHub-MCP-Server/1.0'
});

// Tool implementations
async function getRepoDetails(owner: string, repo: string) {
  try {
    const response = await axios.get(`${GITHUB_BASE_URL}/repos/${owner}/${repo}`, {
      headers: getGithubHeaders()
    });
    
    const repoData = response.data;
    
    return {
      success: true,
      data: {
        id: repoData.id,
        name: repoData.name,
        full_name: repoData.full_name,
        description: repoData.description,
        private: repoData.private,
        html_url: repoData.html_url,
        clone_url: repoData.clone_url,
        language: repoData.language,
        size: repoData.size,
        stars: repoData.stargazers_count,
        watchers: repoData.watchers_count,
        forks: repoData.forks_count,
        open_issues: repoData.open_issues_count,
        default_branch: repoData.default_branch,
        created_at: repoData.created_at,
        updated_at: repoData.updated_at
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

async function listIssues(owner: string, repo: string, state: string = 'open', limit: number = 30) {
  try {
    const response = await axios.get(`${GITHUB_BASE_URL}/repos/${owner}/${repo}/issues`, {
      headers: getGithubHeaders(),
      params: { state, per_page: limit }
    });
    
    const issues = response.data.map((issue: any) => ({
      id: issue.id,
      number: issue.number,
      title: issue.title,
      body: issue.body,
      state: issue.state,
      created_at: issue.created_at,
      updated_at: issue.updated_at,
      html_url: issue.html_url,
      user: {
        login: issue.user.login,
        avatar_url: issue.user.avatar_url
      },
      labels: issue.labels.map((label: any) => ({
        name: label.name,
        color: label.color
      })),
      assignees: issue.assignees.map((assignee: any) => assignee.login)
    }));
    
    return {
      success: true,
      data: {
        issues,
        total_count: issues.length,
        state_filter: state
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

async function createIssue(owner: string, repo: string, title: string, body: string, labels?: string[]) {
  try {
    const issueData: any = { title, body };
    if (labels && labels.length > 0) {
      issueData.labels = labels;
    }
    
    const response = await axios.post(`${GITHUB_BASE_URL}/repos/${owner}/${repo}/issues`, issueData, {
      headers: getGithubHeaders()
    });
    
    const issue = response.data;
    
    return {
      success: true,
      data: {
        id: issue.id,
        number: issue.number,
        title: issue.title,
        body: issue.body,
        state: issue.state,
        html_url: issue.html_url,
        created_at: issue.created_at
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

async function listPullRequests(owner: string, repo: string, state: string = 'open') {
  try {
    const response = await axios.get(`${GITHUB_BASE_URL}/repos/${owner}/${repo}/pulls`, {
      headers: getGithubHeaders(),
      params: { state, per_page: 30 }
    });
    
    const prs = response.data.map((pr: any) => ({
      id: pr.id,
      number: pr.number,
      title: pr.title,
      state: pr.state,
      created_at: pr.created_at,
      updated_at: pr.updated_at,
      html_url: pr.html_url,
      head: {
        ref: pr.head.ref,
        sha: pr.head.sha
      },
      base: {
        ref: pr.base.ref,
        sha: pr.base.sha
      },
      user: {
        login: pr.user.login,
        avatar_url: pr.user.avatar_url
      }
    }));
    
    return {
      success: true,
      data: {
        pull_requests: prs,
        total_count: prs.length,
        state_filter: state
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

async function searchRepositories(query: string, sort: string = 'stars', limit: number = 10) {
  try {
    const response = await axios.get(`${GITHUB_BASE_URL}/search/repositories`, {
      headers: getGithubHeaders(),
      params: { q: query, sort, per_page: limit }
    });
    
    const repos = response.data.items.map((repo: any) => ({
      id: repo.id,
      name: repo.name,
      full_name: repo.full_name,
      description: repo.description,
      html_url: repo.html_url,
      language: repo.language,
      stars: repo.stargazers_count,
      forks: repo.forks_count,
      updated_at: repo.updated_at
    }));
    
    return {
      success: true,
      data: {
        repositories: repos,
        total_count: response.data.total_count,
        query,
        sort_by: sort
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

// MCP endpoints
app.get('/mcp/tools', (req, res) => {
  res.json({ tools: config.tools });
});

app.post('/mcp/call-tool', async (req, res) => {
  const { name, arguments: args } = req.body;
  
  try {
    let result;
    
    switch (name) {
      case 'get_repo_details':
        result = await getRepoDetails(args?.owner, args?.repo);
        break;
      case 'list_issues':
        result = await listIssues(args?.owner, args?.repo, args?.state, args?.limit);
        break;
      case 'create_issue':
        result = await createIssue(args?.owner, args?.repo, args?.title, args?.body, args?.labels);
        break;
      case 'list_pull_requests':
        result = await listPullRequests(args?.owner, args?.repo, args?.state);
        break;
      case 'search_repositories':
        result = await searchRepositories(args?.query, args?.sort, args?.limit);
        break;
      default:
        return res.status(400).json({
          error: `Unknown tool: ${name}`
        });
    }
    
    res.json(result);
  } catch (error: any) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'GitHub MCP Server',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`🐙 GitHub MCP Server running on port ${PORT}`);
  console.log(`🔧 Available tools: ${config.tools.map((t: any) => t.name).join(', ')}`);
});
