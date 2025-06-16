#!/usr/bin/env python3
"""
Plaid MCP Client - Python Implementation
Client for Plaid's remote MCP server following MCP Protocol Standards
Team 28 - Code Paglus - Adya MCP Hackathon
"""

import json
import asyncio
import logging
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("plaid-mcp")

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Configuration loaded successfully")
except FileNotFoundError:
    logger.error("config.json not found. Please create configuration file.")
    config = {}

# Initialize MCP server
server = Server("plaid-mcp-client")

# Plaid configuration
PLAID_REMOTE_URL = config.get("plaid", {}).get("remote_server_url", "https://api.dashboard.plaid.com/mcp/sse")
CLIENT_ID = config.get("authentication", {}).get("client_id", "")
SECRET = config.get("authentication", {}).get("secret", "")

# Generate auth token
auth_token = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
PLAID_HEADERS = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json",
    "User-Agent": "Team28-Plaid-MCP/1.0.0"
}

async def make_plaid_request(tool_name: str, args: Dict) -> Dict:
    """Make request to Plaid remote MCP server"""
    try:
        payload = {
            "tool": tool_name,
            "arguments": args
        }
        
        timeout = aiohttp.ClientTimeout(total=config.get("plaid", {}).get("timeout_ms", 15000) / 1000)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(PLAID_REMOTE_URL, headers=PLAID_HEADERS, json=payload) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    error_msg = f"Plaid API Error ({response.status}): {error_data}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                return await response.json()
    except aiohttp.ClientError as e:
        error_msg = f"Network error calling Plaid MCP: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error calling Plaid MCP: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools following MCP protocol"""
    return [
        Tool(
            name="get_accounts",
            description="Get all connected bank accounts with detailed information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_transactions",
            description="Get transaction history for a specific account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of transactions to retrieve",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": ["account_id", "start_date", "end_date"]
            }
        ),
        Tool(
            name="get_balances",
            description="Get current account balances and available funds",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    }
                },
                "required": ["account_id"]
            }
        ),
        Tool(
            name="get_identity",
            description="Get account holder identity information",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    }
                },
                "required": ["account_id"]
            }
        ),
        Tool(
            name="analyze_spending",
            description="Analyze spending patterns and categorize transactions",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Account identifier"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date for analysis (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "End date for analysis (YYYY-MM-DD)"
                    }
                },
                "required": ["account_id", "start_date", "end_date"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution following MCP protocol"""
    
    try:
        if name == "get_accounts":
            return await get_accounts()
        elif name == "get_transactions":
            return await get_transactions(
                arguments.get("account_id"),
                arguments.get("start_date"),
                arguments.get("end_date"),
                arguments.get("count", 100)
            )
        elif name == "get_balances":
            return await get_balances(arguments.get("account_id"))
        elif name == "get_identity":
            return await get_identity(arguments.get("account_id"))
        elif name == "analyze_spending":
            return await analyze_spending(
                arguments.get("account_id"),
                arguments.get("start_date"),
                arguments.get("end_date")
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

async def get_accounts() -> List[types.TextContent]:
    """Get all connected bank accounts"""
    try:
        logger.info("Getting connected accounts from Plaid")
        result = await make_plaid_request("get_accounts", {})
        
        # Process and enhance the response
        accounts = result.get("accounts", [])
        processed_accounts = []
        
        account_summary = {
            "total_accounts": len(accounts),
            "by_type": {},
            "by_subtype": {},
            "institutions": set()
        }
        
        for account in accounts:
            account_type = account.get("type", "unknown")
            account_subtype = account.get("subtype", "unknown")
            institution = account.get("institution_name", "Unknown")
            
            account_summary["by_type"][account_type] = account_summary["by_type"].get(account_type, 0) + 1
            account_summary["by_subtype"][account_subtype] = account_summary["by_subtype"].get(account_subtype, 0) + 1
            account_summary["institutions"].add(institution)
            
            processed_accounts.append({
                "account_id": account.get("account_id"),
                "name": account.get("name"),
                "official_name": account.get("official_name"),
                "type": account_type,
                "subtype": account_subtype,
                "institution_name": institution,
                "mask": account.get("mask"),
                "balances": account.get("balances", {}),
                "verification_status": account.get("verification_status")
            })
        
        account_summary["institutions"] = list(account_summary["institutions"])
        
        response_data = {
            "success": True,
            "accounts": processed_accounts,
            "summary": account_summary,
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
            "tool": "get_accounts",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_transactions(account_id: str, start_date: str, end_date: str, count: int = 100) -> List[types.TextContent]:
    """Get transaction history for an account"""
    try:
        logger.info(f"Getting transactions for account {account_id}")
        
        args = {
            "account_id": account_id,
            "start_date": start_date,
            "end_date": end_date,
            "count": count
        }
        
        result = await make_plaid_request("get_transactions", args)
        transactions = result.get("transactions", [])
        
        # Analyze transactions
        analysis = {
            "total_transactions": len(transactions),
            "total_amount": 0,
            "by_category": {},
            "by_account": {},
            "date_range": {"start": start_date, "end": end_date}
        }
        
        processed_transactions = []
        
        for transaction in transactions:
            amount = transaction.get("amount", 0)
            category = transaction.get("category", ["Other"])[0] if transaction.get("category") else "Other"
            account = transaction.get("account_id", "unknown")
            
            analysis["total_amount"] += amount
            analysis["by_category"][category] = analysis["by_category"].get(category, 0) + amount
            analysis["by_account"][account] = analysis["by_account"].get(account, 0) + amount
            
            processed_transactions.append({
                "transaction_id": transaction.get("transaction_id"),
                "account_id": transaction.get("account_id"),
                "amount": amount,
                "date": transaction.get("date"),
                "name": transaction.get("name"),
                "merchant_name": transaction.get("merchant_name"),
                "category": transaction.get("category", []),
                "category_id": transaction.get("category_id"),
                "account_owner": transaction.get("account_owner"),
                "location": transaction.get("location", {}),
                "payment_meta": transaction.get("payment_meta", {}),
                "pending": transaction.get("pending", False)
            })
        
        # Sort categories by spending
        analysis["top_spending_categories"] = sorted(
            analysis["by_category"].items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )[:10]
        
        response_data = {
            "success": True,
            "transactions": processed_transactions,
            "analysis": analysis,
            "account_id": account_id,
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
            "account_id": account_id,
            "tool": "get_transactions",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_balances(account_id: str) -> List[types.TextContent]:
    """Get current account balances"""
    try:
        logger.info(f"Getting balances for account {account_id}")
        
        args = {"account_id": account_id}
        result = await make_plaid_request("get_balances", args)
        
        balances = result.get("balances", {})
        
        response_data = {
            "success": True,
            "account_id": account_id,
            "balances": {
                "available": balances.get("available"),
                "current": balances.get("current"),
                "limit": balances.get("limit"),
                "iso_currency_code": balances.get("iso_currency_code", "USD"),
                "unofficial_currency_code": balances.get("unofficial_currency_code")
            },
            "balance_analysis": {
                "available_vs_current_diff": (balances.get("available", 0) - balances.get("current", 0)) if balances.get("available") and balances.get("current") else None,
                "credit_utilization": (balances.get("current", 0) / balances.get("limit", 1)) * 100 if balances.get("limit") and balances.get("limit") > 0 else None,
                "balance_status": "positive" if balances.get("current", 0) > 0 else "negative" if balances.get("current", 0) < 0 else "zero"
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
            "account_id": account_id,
            "tool": "get_balances",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def get_identity(account_id: str) -> List[types.TextContent]:
    """Get account holder identity information"""
    try:
        logger.info(f"Getting identity for account {account_id}")
        
        args = {"account_id": account_id}
        result = await make_plaid_request("get_identity", args)
        
        identity = result.get("identity", {})
        
        response_data = {
            "success": True,
            "account_id": account_id,
            "identity": {
                "names": identity.get("names", []),
                "emails": identity.get("emails", []),
                "phone_numbers": identity.get("phone_numbers", []),
                "addresses": [
                    {
                        "data": addr.get("data", {}),
                        "primary": addr.get("primary", False)
                    } for addr in identity.get("addresses", [])
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
            "account_id": account_id,
            "tool": "get_identity",
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(error_data, indent=2)
        )]

async def analyze_spending(account_id: str, start_date: str, end_date: str) -> List[types.TextContent]:
    """Analyze spending patterns and provide insights"""
    try:
        logger.info(f"Analyzing spending for account {account_id}")
        
        # Get transactions for analysis
        transactions_result = await get_transactions(account_id, start_date, end_date, 500)
        transactions_data = json.loads(transactions_result[0].text)
        
        if not transactions_data.get("success"):
            return transactions_result
        
        transactions = transactions_data["transactions"]
        
        # Advanced spending analysis
        spending_analysis = {
            "period": {"start": start_date, "end": end_date},
            "summary": {},
            "patterns": {},
            "insights": []
        }
        
        # Calculate spending metrics
        total_spending = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
        total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
        net_cash_flow = total_income - total_spending
        
        spending_analysis["summary"] = {
            "total_spending": total_spending,
            "total_income": total_income,
            "net_cash_flow": net_cash_flow,
            "transaction_count": len(transactions),
            "average_transaction": total_spending / len([t for t in transactions if t["amount"] < 0]) if len([t for t in transactions if t["amount"] < 0]) > 0 else 0
        }
        
        # Category analysis
        category_spending = {}
        for transaction in transactions:
            if transaction["amount"] < 0:  # Only spending transactions
                category = transaction.get("category", ["Other"])[0] if transaction.get("category") else "Other"
                category_spending[category] = category_spending.get(category, 0) + abs(transaction["amount"])
        
        # Merchant analysis
        merchant_spending = {}
        for transaction in transactions:
            if transaction["amount"] < 0:
                merchant = transaction.get("merchant_name") or transaction.get("name", "Unknown")
                merchant_spending[merchant] = merchant_spending.get(merchant, 0) + abs(transaction["amount"])
        
        spending_analysis["patterns"] = {
            "top_categories": sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_merchants": sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10],
            "largest_transactions": sorted(
                [{"name": t["name"], "amount": abs(t["amount"]), "date": t["date"]} for t in transactions if t["amount"] < 0],
                key=lambda x: x["amount"],
                reverse=True
            )[:5]
        }
        
        # Generate insights
        if total_spending > total_income:
            spending_analysis["insights"].append("⚠️ Spending exceeds income for this period")
        
        if category_spending:
            top_category = max(category_spending.items(), key=lambda x: x[1])
            spending_analysis["insights"].append(f"💳 Highest spending category: {top_category[0]} (${top_category[1]:.2f})")
        
        if len(transactions) > 0:
            avg_daily_transactions = len(transactions) / max(1, (datetime.fromisoformat(end_date) - datetime.fromisoformat(start_date)).days)
            spending_analysis["insights"].append(f"📊 Average {avg_daily_transactions:.1f} transactions per day")
        
        response_data = {
            "success": True,
            "account_id": account_id,
            "spending_analysis": spending_analysis,
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
            "account_id": account_id,
            "tool": "analyze_spending",
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
                server_name="plaid-mcp-client",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
