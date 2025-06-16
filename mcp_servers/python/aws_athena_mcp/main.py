#!/usr/bin/env python3
"""
AWS Athena MCP Server - Python Implementation
Following MCP Protocol Standards for SQL analytics and data querying
Team 28 - Code Paglus - Adya MCP Hackathon
"""

import json
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aws-athena-mcp")

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Configuration loaded successfully")
except FileNotFoundError:
    logger.error("config.json not found. Please create configuration file.")
    config = {}

# Initialize MCP server
server = Server("aws-athena-mcp")

# AWS Athena configuration
AWS_REGION = config.get("aws", {}).get("region", "us-east-1")
ATHENA_DATABASE = config.get("aws", {}).get("athena", {}).get("database", "default")
ATHENA_WORKGROUP = config.get("aws", {}).get("athena", {}).get("workgroup", "primary")
QUERY_TIMEOUT = config.get("aws", {}).get("athena", {}).get("query_timeout_ms", 300000) // 1000

# Initialize AWS clients
try:
    athena_client = boto3.client('athena', region_name=AWS_REGION)
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    glue_client = boto3.client('glue', region_name=AWS_REGION)
    sts_client = boto3.client('sts', region_name=AWS_REGION)
    logger.info("✅ AWS clients initialized successfully")
except NoCredentialsError:
    logger.error("❌ AWS credentials not found. Please configure AWS credentials.")
    athena_client = None
    s3_client = None
    glue_client = None
    sts_client = None

def get_query_result_location():
    """Generate S3 location for query results"""
    try:
        account_id = sts_client.get_caller_identity()['Account']
        return f"s3://aws-athena-query-results-{AWS_REGION}-{account_id}/"
    except:
        return f"s3://aws-athena-query-results-{AWS_REGION}-default/"

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools following MCP protocol"""
    return [
        Tool(
            name="execute_query",
            description="Execute SQL query against AWS Athena with comprehensive results",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "database": {
                        "type": "string",
                        "description": "Database name (optional, uses config default)",
                        "default": ATHENA_DATABASE
                    },
                    "workgroup": {
                        "type": "string",
                        "description": "Athena workgroup (optional, uses config default)",
                        "default": ATHENA_WORKGROUP
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="list_databases",
            description="List all available databases in the AWS Glue Data Catalog",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_tables",
            description="List tables in a specific database with detailed metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name",
                        "default": ATHENA_DATABASE
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tables to return",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_query_execution",
            description="Get detailed status and metrics for a query execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_id": {
                        "type": "string",
                        "description": "Query execution ID"
                    }
                },
                "required": ["query_id"]
            }
        ),
        Tool(
            name="get_table_metadata",
            description="Get detailed metadata and schema information for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    }
                },
                "required": ["database", "table"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution following MCP protocol"""
    
    try:
        if name == "execute_query":
            return await execute_query(
                arguments.get("sql"),
                arguments.get("database", ATHENA_DATABASE),
                arguments.get("workgroup", ATHENA_WORKGROUP)
            )
        elif name == "list_databases":
            return await list_databases()
        elif name == "list_tables":
            return await list_tables(
                arguments.get("database", ATHENA_DATABASE),
                arguments.get("limit", 100)
            )
        elif name == "get_query_execution":
            return await get_query_execution(arguments.get("query_id"))
        elif name == "get_table_metadata":
            return await get_table_metadata(
                arguments.get("database"),
                arguments.get("table")
            )
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

async def execute_query(sql: str, database: str = None, workgroup: str = None) -> List[types.TextContent]:
    """Execute SQL query against Athena"""
    if not athena_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "AWS Athena client not initialized. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info(f"Executing query: {sql[:100]}...")
        
        target_database = database or ATHENA_DATABASE
        target_workgroup = workgroup or ATHENA_WORKGROUP
        result_location = get_query_result_location()
        
        # Start query execution
        start_response = athena_client.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={'Database': target_database},
            WorkGroup=target_workgroup,
            ResultConfiguration={'OutputLocation': result_location}
        )
        
        query_execution_id = start_response['QueryExecutionId']
        
        # Wait for query completion with timeout
        max_wait_time = QUERY_TIMEOUT
        wait_time = 0
        poll_interval = 2
        
        while wait_time < max_wait_time:
            status_response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            execution = status_response['QueryExecution']
            status = execution['Status']['State']
            
            if status == 'SUCCEEDED':
                # Get query results
                results_response = athena_client.get_query_results(
                    QueryExecutionId=query_execution_id,
                    MaxResults=1000
                )
                
                # Process results
                columns = []
                rows = []
                
                if 'ResultSet' in results_response:
                    result_set = results_response['ResultSet']
                    
                    # Extract column information
                    if 'ColumnInfo' in result_set['ResultSetMetadata']:
                        columns = [
                            {
                                "name": col['Name'],
                                "type": col['Type'],
                                "label": col.get('Label', col['Name'])
                            } for col in result_set['ResultSetMetadata']['ColumnInfo']
                        ]
                    
                    # Extract rows
                    if 'Rows' in result_set:
                        for i, row in enumerate(result_set['Rows']):
                            if i == 0 and not columns:
                                # First row might be headers
                                columns = [{"name": cell.get('VarCharValue', f'col_{j}'), "type": "varchar"} 
                                         for j, cell in enumerate(row['Data'])]
                            else:
                                row_data = {}
                                for j, cell in enumerate(row['Data']):
                                    col_name = columns[j]["name"] if j < len(columns) else f'col_{j}'
                                    row_data[col_name] = cell.get('VarCharValue', '')
                                rows.append(row_data)
                
                # Query statistics
                statistics = execution.get('Statistics', {})
                
                response_data = {
                    "success": True,
                    "query_execution": {
                        "query_execution_id": query_execution_id,
                        "status": "SUCCEEDED",
                        "query": sql,
                        "database": target_database,
                        "workgroup": target_workgroup
                    },
                    "results": {
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows)
                    },
                    "statistics": {
                        "data_scanned_bytes": statistics.get('DataScannedInBytes', 0),
                        "data_scanned_mb": round(statistics.get('DataScannedInBytes', 0) / (1024 * 1024), 2),
                        "execution_time_ms": statistics.get('EngineExecutionTimeInMillis', 0),
                        "query_queue_time_ms": statistics.get('QueryQueueTimeInMillis', 0),
                        "query_planning_time_ms": statistics.get('QueryPlanningTimeInMillis', 0),
                        "service_processing_time_ms": statistics.get('ServiceProcessingTimeInMillis', 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(response_data, indent=2)
                )]
            
            elif status in ['FAILED', 'CANCELLED']:
                error_reason = execution['Status'].get('StateChangeReason', 'Unknown error')
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Query {status.lower()}: {error_reason}",
                        "query_execution_id": query_execution_id,
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                )]
            
            # Query still running
            await asyncio.sleep(poll_interval)
            wait_time += poll_interval
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Query timeout after {max_wait_time} seconds",
                "query_execution_id": query_execution_id,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
        
    except ClientError as e:
        error_data = {
            "success": False,
            "error": f"AWS error: {str(e)}",
            "error_code": e.response.get('Error', {}).get('Code'),
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]
    except Exception as e:
        error_data = {
            "success": False,
            "error": f"Execution error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def list_databases() -> List[types.TextContent]:
    """List available databases"""
    if not glue_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "AWS Glue client not initialized. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info("Listing databases from Glue Data Catalog")
        response = glue_client.get_databases()
        
        databases = []
        total_tables = 0
        
        for db in response.get('DatabaseList', []):
            # Get table count for each database
            try:
                tables_response = glue_client.get_tables(DatabaseName=db['Name'])
                table_count = len(tables_response.get('TableList', []))
                total_tables += table_count
            except:
                table_count = 0
            
            databases.append({
                "name": db['Name'],
                "description": db.get('Description', ''),
                "location_uri": db.get('LocationUri', ''),
                "parameters": db.get('Parameters', {}),
                "table_count": table_count,
                "create_time": db.get('CreateTime', '').isoformat() if db.get('CreateTime') else None
            })
        
        response_data = {
            "success": True,
            "databases": databases,
            "summary": {
                "total_databases": len(databases),
                "total_tables": total_tables
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except ClientError as e:
        error_data = {
            "success": False,
            "error": f"AWS error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def list_tables(database: str = None, limit: int = 100) -> List[types.TextContent]:
    """List tables in a database"""
    if not glue_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "AWS Glue client not initialized. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        target_database = database or ATHENA_DATABASE
        logger.info(f"Listing tables in database {target_database}")
        
        response = glue_client.get_tables(DatabaseName=target_database)
        tables = []
        
        for table in response.get('TableList', [])[:limit]:
            storage_desc = table.get('StorageDescriptor', {})
            
            tables.append({
                "name": table['Name'],
                "database": table['DatabaseName'],
                "table_type": table.get('TableType', ''),
                "storage_descriptor": {
                    "location": storage_desc.get('Location', ''),
                    "input_format": storage_desc.get('InputFormat', ''),
                    "output_format": storage_desc.get('OutputFormat', ''),
                    "serde_info": storage_desc.get('SerdeInfo', {})
                },
                "partition_keys": [
                    {"name": col['Name'], "type": col['Type']} 
                    for col in table.get('PartitionKeys', [])
                ],
                "columns": [
                    {"name": col['Name'], "type": col['Type'], "comment": col.get('Comment', '')} 
                    for col in storage_desc.get('Columns', [])
                ],
                "parameters": table.get('Parameters', {}),
                "create_time": table.get('CreateTime', '').isoformat() if table.get('CreateTime') else None,
                "update_time": table.get('UpdateTime', '').isoformat() if table.get('UpdateTime') else None
            })
        
        response_data = {
            "success": True,
            "tables": tables,
            "database": target_database,
            "summary": {
                "total_tables": len(tables),
                "limit_applied": limit
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except ClientError as e:
        error_data = {
            "success": False,
            "error": f"AWS error: {str(e)}",
            "database": target_database,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_query_execution(query_id: str) -> List[types.TextContent]:
    """Get query execution status and details"""
    if not athena_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "AWS Athena client not initialized. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info(f"Getting execution details for query {query_id}")
        response = athena_client.get_query_execution(QueryExecutionId=query_id)
        execution = response['QueryExecution']
        
        response_data = {
            "success": True,
            "query_execution": {
                "query_execution_id": query_id,
                "query": execution['Query'],
                "status": execution['Status']['State'],
                "state_change_reason": execution['Status'].get('StateChangeReason', ''),
                "submission_time": execution['Status']['SubmissionDateTime'].isoformat(),
                "completion_time": execution['Status'].get('CompletionDateTime', '').isoformat() if execution['Status'].get('CompletionDateTime') else None,
                "database": execution['QueryExecutionContext']['Database'],
                "workgroup": execution['WorkGroup'],
                "result_configuration": execution.get('ResultConfiguration', {}),
                "statistics": {
                    "engine_execution_time_ms": execution['Statistics'].get('EngineExecutionTimeInMillis', 0),
                    "data_processed_bytes": execution['Statistics'].get('DataProcessedInBytes', 0),
                    "data_scanned_bytes": execution['Statistics'].get('DataScannedInBytes', 0),
                    "query_queue_time_ms": execution['Statistics'].get('QueryQueueTimeInMillis', 0),
                    "query_planning_time_ms": execution['Statistics'].get('QueryPlanningTimeInMillis', 0)
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except ClientError as e:
        error_data = {
            "success": False,
            "error": f"AWS error: {str(e)}",
            "query_id": query_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_table_metadata(database: str, table: str) -> List[types.TextContent]:
    """Get detailed table metadata"""
    if not glue_client:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "AWS Glue client not initialized. Check credentials.",
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        )]
    
    try:
        logger.info(f"Getting metadata for table {database}.{table}")
        response = glue_client.get_table(DatabaseName=database, Name=table)
        table_data = response['Table']
        storage_desc = table_data.get('StorageDescriptor', {})
        
        response_data = {
            "success": True,
            "table_metadata": {
                "basic_info": {
                    "name": table_data['Name'],
                    "database": table_data['DatabaseName'],
                    "owner": table_data.get('Owner', ''),
                    "table_type": table_data.get('TableType', ''),
                    "create_time": table_data.get('CreateTime', '').isoformat() if table_data.get('CreateTime') else None,
                    "update_time": table_data.get('UpdateTime', '').isoformat() if table_data.get('UpdateTime') else None
                },
                "storage": {
                    "location": storage_desc.get('Location', ''),
                    "input_format": storage_desc.get('InputFormat', ''),
                    "output_format": storage_desc.get('OutputFormat', ''),
                    "compressed": storage_desc.get('Compressed', False),
                    "serde_info": storage_desc.get('SerdeInfo', {})
                },
                "schema": {
                    "columns": [
                        {
                            "name": col['Name'],
                            "type": col['Type'],
                            "comment": col.get('Comment', '')
                        } for col in storage_desc.get('Columns', [])
                    ],
                    "partition_keys": [
                        {
                            "name": col['Name'],
                            "type": col['Type'],
                            "comment": col.get('Comment', '')
                        } for col in table_data.get('PartitionKeys', [])
                    ]
                },
                "parameters": table_data.get('Parameters', {}),
                "retention": table_data.get('Retention', 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(response_data, indent=2)
        )]
        
    except ClientError as e:
        error_data = {
            "success": False,
            "error": f"AWS error: {str(e)}",
            "table": f"{database}.{table}",
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
                server_name="aws-athena-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
