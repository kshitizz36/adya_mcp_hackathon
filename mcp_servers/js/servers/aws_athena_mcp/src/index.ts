import express from 'express';
import cors from 'cors';
import AWS from 'aws-sdk';
import fs from 'fs';
import path from 'path';

const app = express();
app.use(cors());
app.use(express.json());

// Load configuration
const configPath = path.join(__dirname, '../config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const PORT = config.server.port;

// AWS Configuration
const awsConfig = {
  region: config.aws.region,
  credentials: {
    accessKeyId: config.credentials?.access_key_id || process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: config.credentials?.secret_access_key || process.env.AWS_SECRET_ACCESS_KEY
  }
};

// Initialize AWS services
let athena: AWS.Athena;
let glue: AWS.Glue;
let s3: AWS.S3;
let sts: AWS.STS;

try {
  AWS.config.update(awsConfig);
  athena = new AWS.Athena();
  glue = new AWS.Glue();
  s3 = new AWS.S3();
  sts = new AWS.STS();
  console.log('✅ AWS services initialized successfully');
} catch (error) {
  console.error('❌ Failed to initialize AWS services:', error);
}

// Athena configuration
const ATHENA_DATABASE = config.aws.athena.database;
const ATHENA_WORKGROUP = config.aws.athena.workgroup;
const QUERY_TIMEOUT = config.aws.athena.query_timeout_ms;

interface ToolResponse {
  success: boolean;
  data?: any;
  error?: string;
}

// Get query result location
async function getQueryResultLocation(): Promise<string> {
  try {
    const identity = await sts.getCallerIdentity().promise();
    const accountId = identity.Account;
    return `s3://aws-athena-query-results-${awsConfig.region}-${accountId}/`;
  } catch (error) {
    // Fallback to a default location
    return `s3://aws-athena-query-results-${awsConfig.region}-default/`;
  }
}

// Execute SQL query
async function executeQuery(sql: string, database?: string): Promise<ToolResponse> {
  if (!athena) {
    return { success: false, error: 'AWS Athena not initialized. Check credentials.' };
  }

  try {
    const targetDatabase = database || ATHENA_DATABASE;
    const resultLocation = await getQueryResultLocation();

    // Start query execution
    const startParams: AWS.Athena.StartQueryExecutionInput = {
      QueryString: sql,
      QueryExecutionContext: { Database: targetDatabase },
      WorkGroup: ATHENA_WORKGROUP,
      ResultConfiguration: { OutputLocation: resultLocation }
    };

    const startResult = await athena.startQueryExecution(startParams).promise();
    const queryExecutionId = startResult.QueryExecutionId!;

    // Wait for query completion
    const maxWaitTime = QUERY_TIMEOUT;
    let waitTime = 0;
    const pollInterval = 2000; // 2 seconds

    while (waitTime < maxWaitTime) {
      const statusResult = await athena.getQueryExecution({
        QueryExecutionId: queryExecutionId
      }).promise();

      const status = statusResult.QueryExecution?.Status?.State;

      if (status === 'SUCCEEDED') {
        // Get query results
        const resultsParams: AWS.Athena.GetQueryResultsInput = {
          QueryExecutionId: queryExecutionId,
          MaxResults: 1000
        };

        const results = await athena.getQueryResults(resultsParams).promise();
        
        // Process results
        const columns: string[] = [];
        const rows: any[] = [];

        if (results.ResultSet) {
          // Extract column names
          if (results.ResultSet.ResultSetMetadata?.ColumnInfo) {
            columns.push(...results.ResultSet.ResultSetMetadata.ColumnInfo.map(col => col.Name || ''));
          }

          // Extract rows
          if (results.ResultSet.Rows) {
            results.ResultSet.Rows.forEach((row, index) => {
              if (index === 0 && columns.length === 0) {
                // First row might be headers
                row.Data?.forEach(cell => {
                  columns.push(cell.VarCharValue || '');
                });
              } else {
                const rowData: any = {};
                row.Data?.forEach((cell, cellIndex) => {
                  const colName = columns[cellIndex] || `col_${cellIndex}`;
                  rowData[colName] = cell.VarCharValue || '';
                });
                rows.push(rowData);
              }
            });
          }
        }

        return {
          success: true,
          data: {
            query_execution_id: queryExecutionId,
            status: 'SUCCEEDED',
            columns,
            rows,
            row_count: rows.length,
            data_scanned_bytes: statusResult.QueryExecution?.Statistics?.DataScannedInBytes || 0,
            execution_time_ms: statusResult.QueryExecution?.Statistics?.EngineExecutionTimeInMillis || 0
          }
        };
      } else if (status === 'FAILED' || status === 'CANCELLED') {
        const errorReason = statusResult.QueryExecution?.Status?.StateChangeReason || 'Unknown error';
        return {
          success: false,
          error: `Query ${status.toLowerCase()}: ${errorReason}`
        };
      }

      // Query still running, wait
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      waitTime += pollInterval;
    }

    return {
      success: false,
      error: `Query timeout after ${maxWaitTime}ms`
    };

  } catch (error: any) {
    return {
      success: false,
      error: `Execution error: ${error.message}`
    };
  }
}

// List databases
async function listDatabases(): Promise<ToolResponse> {
  if (!glue) {
    return { success: false, error: 'AWS Glue not initialized. Check credentials.' };
  }

  try {
    const result = await glue.getDatabases().promise();
    const databases = result.DatabaseList?.map(db => ({
      name: db.Name,
      description: db.Description || '',
      create_time: db.CreateTime?.toISOString() || null,
      parameters: db.Parameters || {}
    })) || [];

    return {
      success: true,
      data: {
        databases,
        total_count: databases.length
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Error listing databases: ${error.message}`
    };
  }
}

// List tables
async function listTables(database?: string): Promise<ToolResponse> {
  if (!glue) {
    return { success: false, error: 'AWS Glue not initialized. Check credentials.' };
  }

  try {
    const targetDatabase = database || ATHENA_DATABASE;
    const result = await glue.getTables({ DatabaseName: targetDatabase }).promise();
    
    const tables = result.TableList?.map(table => ({
      name: table.Name,
      database: table.DatabaseName,
      table_type: table.TableType || '',
      create_time: table.CreateTime?.toISOString() || null,
      update_time: table.UpdateTime?.toISOString() || null,
      storage_descriptor: {
        location: table.StorageDescriptor?.Location || '',
        input_format: table.StorageDescriptor?.InputFormat || '',
        output_format: table.StorageDescriptor?.OutputFormat || ''
      },
      partition_keys: table.PartitionKeys?.map(key => key.Name) || [],
      column_count: table.StorageDescriptor?.Columns?.length || 0
    })) || [];

    return {
      success: true,
      data: {
        tables,
        database: targetDatabase,
        total_count: tables.length
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Error listing tables: ${error.message}`
    };
  }
}

// Get query execution status
async function getQueryExecution(queryId: string): Promise<ToolResponse> {
  if (!athena) {
    return { success: false, error: 'AWS Athena not initialized. Check credentials.' };
  }

  try {
    const result = await athena.getQueryExecution({ QueryExecutionId: queryId }).promise();
    const execution = result.QueryExecution;

    if (!execution) {
      return { success: false, error: 'Query execution not found' };
    }

    return {
      success: true,
      data: {
        query_execution_id: queryId,
        query: execution.Query,
        status: execution.Status?.State,
        state_change_reason: execution.Status?.StateChangeReason || '',
        submission_time: execution.Status?.SubmissionDateTime?.toISOString(),
        completion_time: execution.Status?.CompletionDateTime?.toISOString() || null,
        database: execution.QueryExecutionContext?.Database,
        workgroup: execution.WorkGroup,
        statistics: {
          engine_execution_time_ms: execution.Statistics?.EngineExecutionTimeInMillis || 0,
          data_processed_bytes: execution.Statistics?.DataProcessedInBytes || 0,
          data_scanned_bytes: execution.Statistics?.DataScannedInBytes || 0,
          query_queue_time_ms: execution.Statistics?.QueryQueueTimeInMillis || 0,
          query_planning_time_ms: execution.Statistics?.QueryPlanningTimeInMillis || 0
        }
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Error getting query execution: ${error.message}`
    };
  }
}

// Cancel query
async function cancelQuery(queryId: string): Promise<ToolResponse> {
  if (!athena) {
    return { success: false, error: 'AWS Athena not initialized. Check credentials.' };
  }

  try {
    await athena.stopQueryExecution({ QueryExecutionId: queryId }).promise();

    return {
      success: true,
      data: {
        query_execution_id: queryId,
        status: 'CANCELLED',
        message: 'Query cancellation requested'
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: `Error cancelling query: ${error.message}`
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
    let result: ToolResponse;
    
    switch (name) {
      case 'execute_query':
        result = await executeQuery(args?.sql, args?.database);
        break;
      case 'list_databases':
        result = await listDatabases();
        break;
      case 'list_tables':
        result = await listTables(args?.database);
        break;
      case 'get_query_execution':
        result = await getQueryExecution(args?.query_id);
        break;
      case 'cancel_query':
        result = await cancelQuery(args?.query_id);
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
  const awsStatus = athena ? 'healthy' : 'no_credentials';
  
  res.json({ 
    status: 'healthy', 
    service: 'AWS Athena MCP Server',
    aws_status: awsStatus,
    region: awsConfig.region,
    default_database: ATHENA_DATABASE,
    workgroup: ATHENA_WORKGROUP,
    timestamp: new Date().toISOString()
  });
});

app.get('/aws-status', async (req, res) => {
  const status = {
    athena: false,
    s3: false,
    glue: false,
    region: awsConfig.region
  };

  try {
    if (athena) {
      await athena.listWorkGroups({ MaxResults: 1 }).promise();
      status.athena = true;
    }
  } catch (error) {
    // Athena check failed
  }

  try {
    if (s3) {
      await s3.listBuckets().promise();
      status.s3 = true;
    }
  } catch (error) {
    // S3 check failed
  }

  try {
    if (glue) {
      await glue.getDatabases({ MaxResults: 1 }).promise();
      status.glue = true;
    }
  } catch (error) {
    // Glue check failed
  }

  res.json(status);
});

app.listen(PORT, () => {
  console.log(`🗃️  AWS Athena MCP Server running on port ${PORT}`);
  console.log(`🌍 AWS Region: ${awsConfig.region}`);
  console.log(`🗂️  Default Database: ${ATHENA_DATABASE}`);
  console.log(`⚙️  Workgroup: ${ATHENA_WORKGROUP}`);
  console.log(`🔧 Available tools: ${config.tools.map((t: any) => t.name).join(', ')}`);
});
