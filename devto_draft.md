---
title: "I Built an MCP Server for FreshBooks — Here's What I Learned"
published: false
description: "25 tools for the FreshBooks API, built with Python and the official MCP SDK. Invoices, clients, expenses, time tracking, projects, estimates, and reports — all from Claude, Cursor, or any MCP client."
tags: mcp, ai, python, freshbooks
cover_image:
---

FreshBooks has 30 million users. The MCP ecosystem has 19,000+ servers. The best FreshBooks MCP server I could find had 2 GitHub stars and barely worked.

So I built one that does.

## What It Does

[MCP](https://modelcontextprotocol.io/) lets AI assistants interact with external tools directly. With this server installed, you manage your entire freelance business without leaving your AI assistant.

**Before (manual):**
1. Log into FreshBooks
2. Navigate to Invoices → find overdue ones
3. Note the client names and amounts
4. Switch to your AI tool
5. Type out all the details
6. Ask what to do about it

**After (with mcp-freshbooks):**
> "Which invoices are overdue? Draft follow-up messages for each client based on how late they are."

Claude calls `list_invoices` with a status filter, gets the details, and drafts personalized follow-ups — all in one shot.

## 25 Tools, Full Business Coverage

- **Invoices** (6): List, get, create, update, delete, send by email
- **Clients** (4): List, get, create, archive with full contact details
- **Expenses** (3): List, get, create with category and tax support
- **Payments** (2): List, record payments against invoices
- **Time Entries** (2): List, create with project/service association
- **Projects** (2): List, get with budget and billing details
- **Estimates** (2): List, get with line items
- **Reports** (1): Profit & Loss report with date filtering
- **Auth** (3): OAuth2 flow, identity check, connection test

## Technical Decisions Worth Sharing

### Full OAuth2 — No Shortcuts

FreshBooks requires OAuth2. No API keys, no shortcuts. The server handles the entire flow: it spins up a local HTTPS callback server, opens the authorization URL, catches the redirect with the auth code, exchanges it for tokens, and persists them to `~/.mcp-freshbooks/tokens.json`. Token refresh is automatic — you authenticate once and forget about it.

```python
@mcp.tool()
def freshbooks_authenticate() -> str:
    """Start OAuth2 authentication. Returns a URL to open in your browser."""
    config = get_config()
    url = get_auth_url(config)
    # Spins up localhost:8555 HTTPS callback server in background
    start_callback_server(config)
    return f"Open this URL to authorize:\n{url}"
```

This was the hardest part of the build. Most MCP servers assume API keys. When your platform demands OAuth2, you either solve it properly or your server is useless.

### Two APIs, Two Base URLs

FreshBooks has a split API: accounting resources (invoices, clients, expenses) live at `api.freshbooks.com/accounting/account/{account_id}/...`, while project resources (projects, time entries) live at `api.freshbooks.com/projects/business/{business_id}/...`. Different base URLs, different ID types.

The client abstracts this completely:

```python
ACCOUNTING_BASE = "https://api.freshbooks.com/accounting/account"
PROJECTS_BASE = "https://api.freshbooks.com/projects/business"

async def accounting_list(resource, ...):
    account_id, _ = await get_ids()
    url = f"{ACCOUNTING_BASE}/{account_id}/{resource}"
    ...

async def projects_list(resource, ...):
    _, business_id = await get_ids()
    url = f"{PROJECTS_BASE}/{business_id}/{resource}"
    ...
```

The tools never think about which API base to use — they just call the right function.

### Soft Deletes vs Hard Deletes

FreshBooks treats deletion differently depending on the resource. Invoices and estimates can be hard-deleted (actually removed). Clients and expenses can only be soft-deleted by setting `vis_state` to 1 (archived). Delete a client with the wrong endpoint and you get a cryptic 400 error.

```python
async def accounting_delete(resource, resource_id):
    """Hard-delete (invoices, estimates)."""
    ...

async def accounting_soft_delete(resource, resource_id, wrapper_key):
    """Soft-delete via vis_state=1 (clients, expenses)."""
    return await accounting_update(resource, resource_id, wrapper_key, {"vis_state": 1})
```

Each tool uses the correct method — the AI never needs to know about this distinction.

### The search[key] Query Format

FreshBooks uses a non-standard query parameter format for filters: `search[status]=2&search[date_from]=2024-01-01`. Not `status=2`, not `filter[status]=2` — specifically `search[key]`. Get the format wrong and the API silently ignores your filters.

```python
def _build_search_params(filters):
    params = {}
    for key, value in filters.items():
        if isinstance(value, list):
            for v in value:
                params.setdefault(f"search[{key}][]", []).append(str(v))
        else:
            params[f"search[{key}]"] = str(value)
    return params
```

The tools accept clean Python dicts and handle the formatting internally.

## Get Started in 2 Minutes

### Install

```bash
pip install mcp-freshbooks
```

### Create OAuth App

Go to [my.freshbooks.com/#/developer](https://my.freshbooks.com/#/developer), create an app, and note the client ID and secret. Set the redirect URI to `https://localhost:8555/callback`.

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "freshbooks": {
      "command": "mcp-freshbooks",
      "env": {
        "FRESHBOOKS_CLIENT_ID": "your-client-id",
        "FRESHBOOKS_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Then ask Claude to run `freshbooks_authenticate` — it will give you a URL to authorize. One-time setup, tokens auto-refresh after that.

### Claude Code

```bash
claude mcp add freshbooks -- env FRESHBOOKS_CLIENT_ID=id FRESHBOOKS_CLIENT_SECRET=secret mcp-freshbooks
```

### Cursor

Same JSON config as Claude Desktop in `.cursor/mcp.json`.

## What I'd Do Differently

**Add invoice line item support from day one.** The current `create_invoice` accepts line items as a JSON string, which works but isn't the cleanest interface. A dedicated line-item builder would be more ergonomic for the AI.

**Handle plan-gated features more gracefully.** FreshBooks gates features by plan tier — time tracking, projects, and advanced reports require paid plans. The error handling catches 403s and explains this, but detecting plan limits upfront would be smoother.

## Lessons for MCP Server Builders

1. **Solve OAuth2 properly.** If your target platform requires it, don't punt — build the full flow with token persistence and auto-refresh. It's the difference between a demo and a tool people actually use.
2. **Abstract API inconsistencies.** If the platform has split APIs, different deletion behaviors, or non-standard query formats — hide all of it. The AI should never deal with platform quirks.
3. **Handle plan-tier errors.** SaaS platforms gate features by pricing tier. Catch permission errors and explain what's happening instead of returning raw 403s.
4. **Persist tokens securely.** Store tokens in a well-known location (`~/.mcp-freshbooks/`) with clear documentation. Users shouldn't have to re-authenticate every session.

## Links

- **GitHub**: [AlexlaGuardia/mcp-freshbooks](https://github.com/AlexlaGuardia/mcp-freshbooks)
- **PyPI**: [mcp-freshbooks](https://pypi.org/project/mcp-freshbooks/)
- **License**: MIT

---

*This is part of a series of production-grade MCP servers I'm building for underserved SaaS platforms. Also available: [Mailchimp](https://github.com/AlexlaGuardia/mcp-mailchimp), [WooCommerce](https://github.com/AlexlaGuardia/mcp-woocommerce), [ActiveCampaign](https://github.com/AlexlaGuardia/mcp-activecampaign). Follow me here or on [GitHub](https://github.com/AlexlaGuardia) to catch the next one.*
