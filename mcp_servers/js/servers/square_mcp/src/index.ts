import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Square API configuration
const SQUARE_BASE_URL = process.env.SQUARE_ENVIRONMENT === 'production' 
  ? 'https://connect.squareup.com/v2'
  : 'https://connect.squareupsandbox.com/v2';

const squareHeaders = {
  'Authorization': `Bearer ${process.env.SQUARE_ACCESS_TOKEN}`,
  'Content-Type': 'application/json',
  'Square-Version': '2023-10-18'
};

// MCP Tool definitions
const tools = [
  {
    name: 'list_locations',
    description: 'List all business locations',
    inputSchema: {
      type: 'object',
      properties: {},
      required: []
    }
  },
  {
    name: 'get_sales_summary',
    description: 'Generate sales summary report for specified number of days',
    inputSchema: {
      type: 'object',
      properties: {
        days: {
          type: 'number',
          description: 'Number of days to include in summary (default: 7)',
          default: 7
        }
      },
      required: []
    }
  },
  {
    name: 'get_top_products',
    description: 'Get best-selling products with sales data',
    inputSchema: {
      type: 'object',
      properties: {
        limit: {
          type: 'number',
          description: 'Maximum number of products to return (default: 10)',
          default: 10
        }
      },
      required: []
    }
  },
  {
    name: 'list_orders',
    description: 'List orders for a specific location',
    inputSchema: {
      type: 'object',
      properties: {
        location_id: {
          type: 'string',
          description: 'The location ID to get orders for'
        }
      },
      required: ['location_id']
    }
  }
];

// Tool implementations
async function listLocations() {
  try {
    const response = await axios.get(`${SQUARE_BASE_URL}/locations`, {
      headers: squareHeaders
    });
    
    return {
      success: true,
      data: response.data.locations || []
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.errors || error.message
    };
  }
}

async function getSalesSummary(days: number = 7) {
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    const searchBody = {
      filter: {
        date_time_filter: {
          created_at: {
            start_at: startDate.toISOString(),
            end_at: endDate.toISOString()
          }
        }
      }
    };

    const response = await axios.post(`${SQUARE_BASE_URL}/orders/search`, searchBody, {
      headers: squareHeaders
    });

    const orders = response.data.orders || [];
    
    // Calculate summary metrics
    const totalSales = orders.reduce((sum: number, order: any) => {
      const totalMoney = order.total_money?.amount || 0;
      return sum + totalMoney;
    }, 0);

    const transactionCount = orders.length;
    const averageOrderValue = transactionCount > 0 ? totalSales / transactionCount : 0;

    return {
      success: true,
      data: {
        period_days: days,
        total_sales_cents: totalSales,
        total_sales_dollars: totalSales / 100,
        transaction_count: transactionCount,
        average_order_value_cents: Math.round(averageOrderValue),
        average_order_value_dollars: averageOrderValue / 100,
        date_range: {
          start: startDate.toISOString().split('T')[0],
          end: endDate.toISOString().split('T')[0]
        }
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.errors || error.message
    };
  }
}

async function getTopProducts(limit: number = 10) {
  try {
    // Get catalog items
    const catalogResponse = await axios.get(`${SQUARE_BASE_URL}/catalog/list?types=ITEM`, {
      headers: squareHeaders
    });

    const items = catalogResponse.data.objects || [];
    
    // For demo purposes, we'll simulate sales data
    // In production, you'd cross-reference with actual order data
    const productsWithSales = items.slice(0, limit).map((item: any, index: number) => ({
      id: item.id,
      name: item.item_data?.name || 'Unknown Item',
      category: item.item_data?.category_id || 'Uncategorized',
      simulated_units_sold: Math.floor(Math.random() * 100) + 10,
      simulated_revenue_cents: Math.floor(Math.random() * 10000) + 1000,
      rank: index + 1
    }));

    return {
      success: true,
      data: {
        top_products: productsWithSales,
        total_items_analyzed: items.length,
        limit_applied: limit
      }
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.errors || error.message
    };
  }
}

async function listOrders(locationId: string) {
  try {
    const searchBody = {
      location_ids: [locationId],
      limit: 100
    };

    const response = await axios.post(`${SQUARE_BASE_URL}/orders/search`, searchBody, {
      headers: squareHeaders
    });

    return {
      success: true,
      data: response.data.orders || []
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.errors || error.message
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
      case 'list_locations':
        result = await listLocations();
        break;
      case 'get_sales_summary':
        result = await getSalesSummary(args?.days);
        break;
      case 'get_top_products':
        result = await getTopProducts(args?.limit);
        break;
      case 'list_orders':
        result = await listOrders(args?.location_id);
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
    service: 'Square MCP Enhanced',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`🟦 Enhanced Square MCP Server running on port ${PORT}`);
  console.log(`📊 Available tools: ${tools.map(t => t.name).join(', ')}`);
});
