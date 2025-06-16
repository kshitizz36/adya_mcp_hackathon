#!/usr/bin/env python3
"""
H2O.ai MCP Server - Python Implementation
Following MCP Protocol Standards for ML operations
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
logger = logging.getLogger("h2o-ai-mcp")

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Configuration loaded successfully")
except FileNotFoundError:
    logger.error("config.json not found. Please create configuration file.")
    config = {}

# Initialize MCP server
server = Server("h2o-ai-mcp")

# H2O.ai configuration
H2O_BASE_URL = config.get("h2o", {}).get("default_cluster_url", "http://localhost:54321")
H2O_AUTH = aiohttp.BasicAuth(
    config.get("authentication", {}).get("username", "admin"),
    config.get("authentication", {}).get("password", "admin")
)

# Connection state
is_connected = False
cluster_info = None

async def make_h2o_request(endpoint: str, timeout: int = 30) -> Dict:
    """Make authenticated request to H2O.ai cluster"""
    url = f"{H2O_BASE_URL}{endpoint}"
    
    try:
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.get(url, auth=H2O_AUTH) as response:
                if response.status >= 400:
                    error_msg = f"H2O API error ({response.status}): {await response.text()}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return await response.json()
    except aiohttp.ClientError as e:
        error_msg = f"Network error calling H2O API: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error calling H2O API: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools following MCP protocol"""
    return [
        Tool(
            name="connect_to_cluster",
            description="Connect to H2O.ai cluster and verify connectivity",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "H2O cluster URL (optional, uses config default)",
                        "format": "uri"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_models",
            description="List all available machine learning models in the cluster",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_frames",
            description="List all data frames available in the cluster",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of frames to return",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_model_details",
            description="Get comprehensive information about a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The model ID to get details for"
                    }
                },
                "required": ["model_id"]
            }
        ),
        Tool(
            name="get_cluster_status",
            description="Get detailed cluster health and performance metrics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_frame_summary",
            description="Get statistical summary of a data frame",
            inputSchema={
                "type": "object",
                "properties": {
                    "frame_id": {
                        "type": "string",
                        "description": "The frame ID to summarize"
                    }
                },
                "required": ["frame_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution following MCP protocol"""
    
    try:
        if name == "connect_to_cluster":
            url = arguments.get("url")
            return await connect_to_cluster(url)
        elif name == "list_models":
            return await list_models()
        elif name == "list_frames":
            limit = arguments.get("limit", 50)
            return await list_frames(limit)
        elif name == "get_model_details":
            model_id = arguments.get("model_id")
            return await get_model_details(model_id)
        elif name == "get_cluster_status":
            return await get_cluster_status()
        elif name == "get_frame_summary":
            frame_id = arguments.get("frame_id")
            return await get_frame_summary(frame_id)
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

async def connect_to_cluster(url: Optional[str] = None) -> List[types.TextContent]:
    """Connect to H2O.ai cluster"""
    global is_connected, cluster_info, H2O_BASE_URL
    
    try:
        if url:
            H2O_BASE_URL = url
        
        logger.info(f"Connecting to H2O cluster at {H2O_BASE_URL}")
        result = await make_h2o_request("/3/Cloud")
        
        is_connected = True
        cluster_info = result
        
        response_data = {
            "success": True,
            "connected": True,
            "cluster_url": H2O_BASE_URL,
            "cluster_info": {
                "version": cluster_info.get("version", "Unknown"),
                "build_number": cluster_info.get("build_number", "Unknown"),
                "build_age": cluster_info.get("build_age", "Unknown"),
                "nodes": len(cluster_info.get("nodes", [])),
                "status": "Connected",
                "cloud_healthy": cluster_info.get("healthy", False),
                "cloud_size": cluster_info.get("cloud_size", 0),
                "consensus": cluster_info.get("consensus", False)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        is_connected = False
        error_data = {
            "success": False,
            "error": f"Failed to connect to H2O cluster: {str(e)}",
            "cluster_url": H2O_BASE_URL,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def list_models(limit: int = 100) -> List[types.TextContent]:
    """List all available ML models"""
    if not is_connected:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Not connected to H2O cluster. Please connect first.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info("Listing H2O models")
        result = await make_h2o_request("/3/Models")
        models = result.get("models", [])
        
        processed_models = []
        model_summary = {"total": len(models), "by_algorithm": {}, "by_status": {}}
        
        for model in models[:limit]:
            algorithm = model.get("algo", "Unknown")
            status = model.get("job", {}).get("status", "Unknown")
            
            # Count by algorithm and status
            model_summary["by_algorithm"][algorithm] = model_summary["by_algorithm"].get(algorithm, 0) + 1
            model_summary["by_status"][status] = model_summary["by_status"].get(status, 0) + 1
            
            model_data = {
                "model_id": model.get("model_id", {}).get("name", "Unknown"),
                "algorithm": algorithm,
                "training_frame": model.get("data_frame", {}).get("name", "Unknown"),
                "validation_frame": model.get("validation_frame", {}).get("name") if model.get("validation_frame") else None,
                "status": status,
                "creation_time": model.get("timestamp"),
                "training_time_ms": model.get("run_time", 0),
                "model_size_bytes": model.get("model_size", 0),
                "parameters": {
                    "ntrees": model.get("parameters", {}).get("ntrees"),
                    "max_depth": model.get("parameters", {}).get("max_depth"),
                    "learn_rate": model.get("parameters", {}).get("learn_rate")
                } if model.get("parameters") else {}
            }
            
            processed_models.append(model_data)
        
        response_data = {
            "success": True,
            "models": processed_models,
            "summary": model_summary,
            "total_count": len(models),
            "returned_count": len(processed_models),
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": f"Failed to list models: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def list_frames(limit: int = 50) -> List[types.TextContent]:
    """List all data frames"""
    if not is_connected:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Not connected to H2O cluster. Please connect first.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info("Listing H2O data frames")
        result = await make_h2o_request("/3/Frames")
        frames = result.get("frames", [])
        
        processed_frames = []
        total_size = 0
        total_rows = 0
        
        for frame in frames[:limit]:
            frame_size = frame.get("byte_size", 0)
            frame_rows = frame.get("rows", 0)
            
            total_size += frame_size
            total_rows += frame_rows
            
            frame_data = {
                "frame_id": frame.get("frame_id", {}).get("name", "Unknown"),
                "rows": frame_rows,
                "columns": len(frame.get("columns", [])),
                "size_bytes": frame_size,
                "size_mb": round(frame_size / (1024 * 1024), 2) if frame_size > 0 else 0,
                "checksum": frame.get("checksum"),
                "is_text": frame.get("is_text", False),
                "column_types": [col.get("type") for col in frame.get("columns", [])[:10]],  # First 10 column types
                "column_names": [col.get("label") for col in frame.get("columns", [])[:10]]   # First 10 column names
            }
            
            processed_frames.append(frame_data)
        
        response_data = {
            "success": True,
            "frames": processed_frames,
            "summary": {
                "total_frames": len(frames),
                "returned_frames": len(processed_frames),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_rows": total_rows
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
            "error": f"Failed to list frames: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_model_details(model_id: str) -> List[types.TextContent]:
    """Get detailed information about a specific model"""
    if not is_connected:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Not connected to H2O cluster. Please connect first.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info(f"Getting details for model {model_id}")
        result = await make_h2o_request(f"/3/Models/{model_id}")
        models = result.get("models", [])
        
        if not models:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Model {model_id} not found",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            )]
        
        model = models[0]
        output = model.get("output", {})
        
        # Extract performance metrics
        metrics = {}
        if "training_metrics" in output:
            training_metrics = output["training_metrics"]
            metrics["training"] = {
                "mse": training_metrics.get("MSE"),
                "rmse": training_metrics.get("RMSE"),
                "mae": training_metrics.get("mean_absolute_error"),
                "r2": training_metrics.get("r2"),
                "auc": training_metrics.get("AUC"),
                "accuracy": training_metrics.get("accuracy")
            }
        
        if "validation_metrics" in output:
            validation_metrics = output["validation_metrics"]
            metrics["validation"] = {
                "mse": validation_metrics.get("MSE"),
                "rmse": validation_metrics.get("RMSE"),
                "mae": validation_metrics.get("mean_absolute_error"),
                "r2": validation_metrics.get("r2"),
                "auc": validation_metrics.get("AUC"),
                "accuracy": validation_metrics.get("accuracy")
            }
        
        response_data = {
            "success": True,
            "model_details": {
                "model_id": model.get("model_id", {}).get("name"),
                "algorithm": model.get("algo"),
                "parameters": model.get("parameters", {}),
                "training_frame": model.get("data_frame", {}).get("name"),
                "validation_frame": model.get("validation_frame", {}).get("name") if model.get("validation_frame") else None,
                "status": model.get("job", {}).get("status"),
                "training_time_ms": model.get("run_time", 0),
                "model_size_bytes": model.get("model_size", 0),
                "metrics": metrics,
                "variable_importances": output.get("variable_importances", {}).get("data") if output.get("variable_importances") else None,
                "model_summary": output.get("model_summary"),
                "scoring_history": output.get("scoring_history")
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
            "error": f"Failed to get model details: {str(e)}",
            "model_id": model_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_cluster_status() -> List[types.TextContent]:
    """Get cluster status and health metrics"""
    try:
        logger.info("Getting cluster status")
        
        # Get multiple endpoints for comprehensive status
        cloud_result = await make_h2o_request("/3/Cloud")
        
        try:
            timeline_result = await make_h2o_request("/3/Timeline")
            recent_events = timeline_result.get("events", [])[:5]
        except:
            recent_events = []
        
        try:
            profiler_result = await make_h2o_request("/3/Profiler")
            profiler_data = profiler_result
        except:
            profiler_data = {}
        
        # Process node information
        nodes_info = []
        total_memory = 0
        free_memory = 0
        
        for node in cloud_result.get("nodes", []):
            node_memory = {
                "free": node.get("free_mem", 0),
                "total": node.get("max_mem", 0),
                "used": node.get("max_mem", 0) - node.get("free_mem", 0),
                "used_percent": round(((node.get("max_mem", 1) - node.get("free_mem", 0)) / node.get("max_mem", 1)) * 100, 2)
            }
            
            total_memory += node.get("max_mem", 0)
            free_memory += node.get("free_mem", 0)
            
            nodes_info.append({
                "name": node.get("h2o"),
                "ip_port": node.get("ip_port"),
                "healthy": node.get("healthy", False),
                "last_ping": node.get("last_ping"),
                "memory": node_memory,
                "num_cpus": node.get("num_cpus", 0),
                "cpus_allowed": node.get("cpus_allowed", 0)
            })
        
        # Calculate cluster-wide memory usage
        cluster_memory = {
            "total_bytes": total_memory,
            "free_bytes": free_memory,
            "used_bytes": total_memory - free_memory,
            "used_percent": round(((total_memory - free_memory) / total_memory * 100), 2) if total_memory > 0 else 0,
            "total_gb": round(total_memory / (1024**3), 2),
            "free_gb": round(free_memory / (1024**3), 2),
            "used_gb": round((total_memory - free_memory) / (1024**3), 2)
        }
        
        response_data = {
            "success": True,
            "cluster_status": {
                "healthy": cloud_result.get("healthy", False),
                "version": cloud_result.get("version"),
                "build_number": cloud_result.get("build_number"),
                "uptime_ms": cloud_result.get("cloud_uptime_millis", 0),
                "cloud_size": cloud_result.get("cloud_size", 0),
                "consensus": cloud_result.get("consensus", False),
                "locked": cloud_result.get("locked", False)
            },
            "memory_usage": cluster_memory,
            "nodes": nodes_info,
            "recent_activity": recent_events,
            "profiler_data": profiler_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": f"Failed to get cluster status: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_frame_summary(frame_id: str) -> List[types.TextContent]:
    """Get statistical summary of a data frame"""
    if not is_connected:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Not connected to H2O cluster. Please connect first.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info(f"Getting summary for frame {frame_id}")
        
        # Get frame details
        frame_result = await make_h2o_request(f"/3/Frames/{frame_id}")
        frames = frame_result.get("frames", [])
        
        if not frames:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Frame {frame_id} not found",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            )]
        
        frame = frames[0]
        
        # Get frame summary statistics
        try:
            summary_result = await make_h2o_request(f"/3/Frames/{frame_id}/summary")
            summary_data = summary_result.get("frames", [{}])[0] if summary_result.get("frames") else {}
        except:
            summary_data = {}
        
        # Process column information
        columns_info = []
        for col in frame.get("columns", []):
            col_info = {
                "name": col.get("label"),
                "type": col.get("type"),
                "missing_count": col.get("missing_count", 0),
                "zero_count": col.get("zero_count", 0),
                "positive_infinity_count": col.get("positive_infinity_count", 0),
                "negative_infinity_count": col.get("negative_infinity_count", 0),
                "mins": col.get("mins"),
                "maxs": col.get("maxs"),
                "mean": col.get("mean"),
                "sigma": col.get("sigma")
            }
            columns_info.append(col_info)
        
        response_data = {
            "success": True,
            "frame_summary": {
                "frame_id": frame.get("frame_id", {}).get("name"),
                "rows": frame.get("rows", 0),
                "columns": len(frame.get("columns", [])),
                "size_bytes": frame.get("byte_size", 0),
                "size_mb": round(frame.get("byte_size", 0) / (1024 * 1024), 2),
                "is_text": frame.get("is_text", False),
                "checksum": frame.get("checksum"),
                "columns_detail": columns_info,
                "data_quality": {
                    "total_missing_values": sum(col.get("missing_count", 0) for col in frame.get("columns", [])),
                    "columns_with_missing": len([col for col in frame.get("columns", []) if col.get("missing_count", 0) > 0]),
                    "missing_percentage": round(sum(col.get("missing_count", 0) for col in frame.get("columns", [])) / (frame.get("rows", 1) * len(frame.get("columns", []))) * 100, 2) if frame.get("rows", 0) > 0 else 0
                }
            },
            "statistical_summary": summary_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except Exception as e:
        error_data = {
            "success": False,
            "error": f"Failed to get frame summary: {str(e)}",
            "frame_id": frame_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def main():
    """Run the MCP server using stdin/stdout streams"""
    from mcp.server.stdio import stdio_server
    
    # Auto-connect if configured
    if config.get("h2o", {}).get("auto_connect", False):
        try:
            await connect_to_cluster()
        except Exception as e:
            logger.warning(f"Auto-connect failed: {e}")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="h2o-ai-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
