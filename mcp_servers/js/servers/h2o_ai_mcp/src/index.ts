import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3002;

app.use(cors());
app.use(express.json());

// H2O.ai configuration
const H2O_BASE_URL = process.env.H2O_CLUSTER_URL || 'http://localhost:54321';
const H2O_USERNAME = process.env.H2O_USERNAME || 'admin';
const H2O_PASSWORD = process.env.H2O_PASSWORD || 'admin';

// Connection state
let isConnected = false;
let clusterInfo: any = null;

// MCP Tool definitions
const tools = [
  {
    name: 'connect_to_cluster',
    description: 'Connect to H2O.ai cluster',
    inputSchema: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'H2O cluster URL (optional, uses env default)'
        }
      },
      required: []
    }
  },
  {
    name: 'list_models',
    description: 'List all available ML models in the cluster',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    }
  },
  {
    name: 'list_frames',
    description: 'List all data frames in the cluster',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    }
  },
  {
    name: 'get_model_details',
    description: 'Get detailed information about a specific model',
    inputSchema: {
      type: 'object',
      properties: {
        model_id: {
          type: 'string',
          description: 'The model ID to get details for'
        }
      },
      required: ['model_id']
    }
  },
  {
    name: 'get_cluster_status',
    description: 'Get current cluster status and performance metrics',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    }
  }
];

// H2O.ai API client functions
async function connectToCluster(url?: string) {
  const clusterUrl = url || H2O_BASE_URL;
  
  try {
    // Test connection by getting cluster status
    const response = await axios.get(`${clusterUrl}/3/Cloud`, {
      timeout: 10000,
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    isConnected = true;
    clusterInfo = response.data;
    
    return {
      success: true,
      data: {
        connected: true,
        cluster_url: clusterUrl,
        cluster_info: {
          version: clusterInfo.version || 'Unknown',
          build_number: clusterInfo.build_number || 'Unknown',
          nodes: clusterInfo.nodes?.length || 0,
          status: 'Connected'
        }
      }
    };
  } catch (error: any) {
    isConnected = false;
    return {
      success: false,
      error: `Failed to connect to H2O cluster: ${error.message}`
    };
  }
}

async function listModels() {
  if (!isConnected) {
    return {
      success: false,
      error: 'Not connected to H2O cluster. Please connect first.'
    };
  }
  
  try {
    const response = await axios.get(`${H2O_BASE_URL}/3/Models`, {
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    const models = response.data.models || [];
    
    return {
      success: true,
      data: {
        models: models.map((model: any) => ({
          model_id: model.model_id?.name || 'Unknown',
          algorithm: model.algo || 'Unknown',
          training_frame: model.data_frame?.name || 'Unknown',
          status: model.job?.status || 'Unknown',
          creation_time: model.timestamp || null
        })),
        total_count: models.length
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Failed to list models: ${error.message}`
    };
  }
}

async function listFrames() {
  if (!isConnected) {
    return {
      success: false,
      error: 'Not connected to H2O cluster. Please connect first.'
    };
  }
  
  try {
    const response = await axios.get(`${H2O_BASE_URL}/3/Frames`, {
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    const frames = response.data.frames || [];
    
    return {
      success: true,
      data: {
        frames: frames.map((frame: any) => ({
          frame_id: frame.frame_id?.name || 'Unknown',
          rows: frame.rows || 0,
          columns: frame.columns?.length || 0,
          size_bytes: frame.byte_size || 0,
          checksum: frame.checksum || null
        })),
        total_count: frames.length
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Failed to list frames: ${error.message}`
    };
  }
}

async function getModelDetails(modelId: string) {
  if (!isConnected) {
    return {
      success: false,
      error: 'Not connected to H2O cluster. Please connect first.'
    };
  }
  
  try {
    const response = await axios.get(`${H2O_BASE_URL}/3/Models/${modelId}`, {
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    const model = response.data.models?.[0];
    if (!model) {
      return {
        success: false,
        error: `Model ${modelId} not found`
      };
    }
    
    return {
      success: true,
      data: {
        model_id: model.model_id?.name,
        algorithm: model.algo,
        parameters: model.parameters || {},
        metrics: model.output || {},
        training_frame: model.data_frame?.name,
        validation_frame: model.validation_frame?.name,
        status: model.job?.status,
        training_time_ms: model.run_time || 0
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Failed to get model details: ${error.message}`
    };
  }
}

async function getClusterStatus() {
  try {
    const cloudResponse = await axios.get(`${H2O_BASE_URL}/3/Cloud`, {
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    const timelineResponse = await axios.get(`${H2O_BASE_URL}/3/Timeline`, {
      auth: {
        username: H2O_USERNAME,
        password: H2O_PASSWORD
      }
    });
    
    return {
      success: true,
      data: {
        cluster_healthy: cloudResponse.data.healthy || false,
        version: cloudResponse.data.version,
        uptime_ms: cloudResponse.data.cloud_uptime_millis || 0,
        nodes: cloudResponse.data.nodes?.map((node: any) => ({
          name: node.h2o,
          ip_port: node.ip_port,
          healthy: node.healthy,
          last_ping: node.last_ping,
          memory_usage: {
            free: node.free_mem,
            total: node.max_mem,
            used_percent: Math.round(((node.max_mem - node.free_mem) / node.max_mem) * 100)
          }
        })) || [],
        recent_activity: timelineResponse.data.events?.slice(0, 5) || []
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Failed to get cluster status: ${error.message}`
    };
  }
}

// MCP endpoints
app.get('/mcp/tools', (req, res) => {
  res.json({ tools });
});

app.post('/mcp/call-tool', async (req, res) => {
  const { name, arguments: args } = req.body;
  
  try {
    let result;
    
    switch (name) {
      case 'connect_to_cluster':
        result = await connectToCluster(args?.url);
        break;
      case 'list_models':
        result = await listModels();
        break;
      case 'list_frames':
        result = await listFrames();
        break;
      case 'get_model_details':
        result = await getModelDetails(args?.model_id);
        break;
      case 'get_cluster_status':
        result = await getClusterStatus();
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
    service: 'H2O.ai MCP Server',
    connected_to_cluster: isConnected,
    cluster_url: H2O_BASE_URL,
    timestamp: new Date().toISOString()
  });
});

// Auto-connect on startup
connectToCluster().then(result => {
  if (result.success) {
    console.log('✅ Auto-connected to H2O cluster');
  } else {
    console.log('⚠️  Failed to auto-connect to H2O cluster:', result.error);
  }
});

app.listen(PORT, () => {
  console.log(`🤖 H2O.ai MCP Server running on port ${PORT}`);
  console.log(`🔧 Available tools: ${tools.map(t => t.name).join(', ')}`);
});
