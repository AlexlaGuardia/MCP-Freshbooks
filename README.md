# mcp-freshbooks

Production-grade MCP server for [FreshBooks](https://www.freshbooks.com/) — 53 tools for invoices, clients, expenses, payments, time tracking, projects, estimates, financial reports, and smart workflows.

## Features

- **53 tools** covering the full FreshBooks accounting workflow
- **Smart workflow tools** — convert estimates to invoices, invoice unbilled time, find overdue clients, get full client summaries
- **5 financial reports** — P&L, tax summary, accounts aging, balance sheet, payments collected
- **OAuth2 authentication** with automatic token refresh
- **Clean output** — summarized lists, formatted details
- **Production-grade** error handling and rate limit awareness
- **Zero cost** — uses FreshBooks free developer program

## Tools

| Category | Tools | Count |
|----------|-------|-------|
| **Auth** | `freshbooks_authenticate`, `freshbooks_authenticate_with_code`, `freshbooks_whoami` | 3 |
| **Invoices** | `list_invoices`, `get_invoice`, `create_invoice`, `update_invoice`, `send_invoice`, `delete_invoice` | 6 |
| **Recurring** | `list_recurring_invoices`, `create_recurring_invoice`, `update_recurring_invoice` | 3 |
| **Clients** | `list_clients`, `get_client`, `create_client`, `update_client`, `delete_client` | 5 |
| **Estimates** | `list_estimates`, `get_estimate`, `create_estimate`, `update_estimate`, `send_estimate` | 5 |
| **Expenses** | `list_expenses`, `get_expense`, `create_expense`, `update_expense`, `delete_expense` | 5 |
| **Payments** | `list_payments`, `get_payment`, `create_payment` | 3 |
| **Time Tracking** | `list_time_entries`, `get_time_entry`, `create_time_entry`, `update_time_entry`, `delete_time_entry` | 5 |
| **Projects** | `list_projects`, `get_project`, `create_project`, `update_project` | 4 |
| **Reports** | `get_profit_loss`, `get_tax_summary`, `get_accounts_aging`, `get_balance_sheet`, `get_payments_collected` | 5 |
| **Items** | `list_items`, `create_item` | 2 |
| **Categories** | `list_expense_categories` | 1 |
| **Taxes** | `list_taxes` | 1 |
| **Workflows** | `convert_estimate_to_invoice`, `get_overdue_invoices`, `get_unbilled_time`, `invoice_from_time`, `client_summary` | 5 |

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

## Usage Examples

**Who owes me money?**
```
Use get_overdue_invoices to see all past-due clients and total outstanding
```

**Convert a proposal to an invoice:**
```
Use convert_estimate_to_invoice to turn estimate 456 into a ready-to-send invoice
```

**Find unbilled work:**
```
Use get_unbilled_time to find time entries not yet on any invoice
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
├── server.py   # MCP server with 47 tool definitions
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
