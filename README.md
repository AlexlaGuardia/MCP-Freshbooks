# mcp-freshbooks
[![MCPize](https://mcpize.com/badge/@AlexlaGuardia/freshbooks)](https://mcpize.com/mcp/freshbooks)

Production-grade MCP server for [FreshBooks](https://www.freshbooks.com/) — 25 tools for invoices, clients, expenses, payments, time tracking, projects, estimates, and financial reports.

## Features

- **25 tools** covering the full FreshBooks accounting workflow
- **OAuth2 authentication** with automatic token refresh
- **Clean output** — summarized lists, formatted details
- **Production-grade** error handling and rate limit awareness
- **Zero cost** — uses FreshBooks free developer program

## Tools

| Category | Tools | Description |
|----------|-------|-------------|
| **Auth** | `freshbooks_authenticate`, `freshbooks_authenticate_with_code`, `freshbooks_whoami` | OAuth2 flow + identity |
| **Invoices** | `list_invoices`, `get_invoice`, `create_invoice`, `update_invoice`, `send_invoice`, `delete_invoice` | Full invoice lifecycle |
| **Clients** | `list_clients`, `get_client`, `create_client`, `update_client` | Client management |
| **Expenses** | `list_expenses`, `get_expense`, `create_expense` | Expense tracking |
| **Payments** | `list_payments`, `create_payment` | Payment recording |
| **Time Tracking** | `list_time_entries`, `create_time_entry` | Time entry management |
| **Projects** | `list_projects`, `create_project` | Project management |
| **Estimates** | `list_estimates`, `create_estimate` | Estimate creation |
| **Reports** | `get_report` | Profit & loss, tax summary, payments collected |

## Quick Start

### 1. Install

```bash
pip install mcp-freshbooks
```

Or from source:

```bash
git clone https://github.com/AlexlaGuardia/mcp-freshbooks.git
cd mcp-freshbooks
pip install .
```

### 2. Get FreshBooks API Credentials

1. Sign up at [freshbooks.com/pages/developer-signup](https://www.freshbooks.com/pages/developer-signup)
2. Create an OAuth app in the developer portal
3. Set redirect URI to `https://localhost:8555/callback`
4. Copy your Client ID and Client Secret

### 3. Configure

```bash
export FRESHBOOKS_CLIENT_ID=your_client_id
export FRESHBOOKS_CLIENT_SECRET=your_client_secret
export FRESHBOOKS_REDIRECT_URI=https://localhost:8555/callback
```

### 4. Add to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "freshbooks": {
      "command": "mcp-freshbooks",
      "env": {
        "FRESHBOOKS_CLIENT_ID": "your_client_id",
        "FRESHBOOKS_CLIENT_SECRET": "your_client_secret",
        "FRESHBOOKS_REDIRECT_URI": "https://localhost:8555/callback"
      }
    }
  }
}
```

### 5. Authenticate

Use the `freshbooks_authenticate` tool on first use. It will give you a URL to open in your browser. After authorizing, tokens are saved to `~/.mcp-freshbooks/tokens.json` and auto-refresh.

## Connect via MCPize

Use this MCP server instantly with no local installation:

```bash
npx -y mcpize connect @AlexlaGuardia/freshbooks --client claude
```

Or connect at: **https://mcpize.com/mcp/freshbooks**

## Usage Examples

**List overdue invoices:**
```
Use list_invoices with status "outstanding"
```

**Create and send an invoice:**
```
Create an invoice for client 12345 with a line item for "Web Development" at $1,500, then send it
```

**Check profitability:**
```
Get the profit and loss report for Q1 2026
```

**Track time:**
```
Create a 2-hour time entry for project 789 with note "API integration work"
```

## Architecture

```
src/mcp_freshbooks/
├── server.py   # MCP server with 25 tool definitions
├── client.py   # FreshBooks API client (httpx async)
└── auth.py     # OAuth2 flow + token persistence
```

The server uses the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) with FastMCP for clean tool registration. All API calls go through the async client with automatic token refresh.

## Requirements

- Python 3.10+
- FreshBooks account (free trial works for development)
- FreshBooks OAuth app credentials

## License

MIT