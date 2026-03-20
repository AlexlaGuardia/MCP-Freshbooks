"""MCP server for FreshBooks — 25 tools for accounting, invoicing, and business management."""

import json
import functools
import threading
from mcp.server.fastmcp import FastMCP

import httpx

from . import auth, client

mcp = FastMCP(
    "freshbooks",
    instructions="Production-grade MCP server for FreshBooks. Manage invoices, clients, expenses, payments, time tracking, projects, estimates, and reports.",
)


# ─── Formatting helpers ───

def _fmt(data: dict | list | bool, label: str = "") -> str:
    """Format API response for clean tool output."""
    if isinstance(data, bool):
        return f"{label}: {'success' if data else 'failed'}"
    return json.dumps(data, indent=2, default=str)


def _summarize_list(result: dict, resource_key: str, fields: list[str]) -> str:
    """Summarize a list response with key fields."""
    items = result.get(resource_key, [])
    total = result.get("total", len(items))
    page = result.get("page", 1)
    pages = result.get("pages", 1)
    lines = [f"Page {page}/{pages} ({total} total)\n"]
    for item in items:
        parts = []
        for f in fields:
            val = item.get(f)
            if val is not None:
                if isinstance(val, dict) and "amount" in val:
                    val = f"${val['amount']} {val.get('code', '')}"
                parts.append(f"{f}: {val}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _handle_errors(func):
    """Decorator to catch API errors and return clean messages."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 403:
                return f"Error: Access denied (HTTP 403). This feature may require a paid FreshBooks plan."
            if status == 404:
                return f"Error: Resource not found (HTTP 404)."
            if status == 401:
                return f"Error: Authentication expired. Run freshbooks_authenticate again."
            try:
                body = e.response.json()
                errors = body.get("response", {}).get("errors", [])
                if errors:
                    msgs = [err.get("message", str(err)) for err in errors]
                    return f"Error: {'; '.join(msgs)}"
            except Exception:
                pass
            return f"Error: HTTP {status} — {e.response.text[:200]}"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
    return wrapper


# ─── Auth Tools ───

@mcp.tool()
def freshbooks_authenticate() -> str:
    """Start FreshBooks OAuth2 authentication. Returns a URL to open in your browser. After authorizing, tokens are saved automatically."""
    config = auth.get_config()
    url = auth.get_auth_url(config)
    port = int(config["redirect_uri"].split(":")[-1].split("/")[0])

    def _run_server():
        auth.start_callback_server(config, port)

    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()

    return (
        f"Open this URL in your browser to authorize:\n\n{url}\n\n"
        f"Waiting for callback on localhost:{port}..."
    )


@mcp.tool()
def freshbooks_authenticate_with_code(code: str) -> str:
    """Complete authentication with an authorization code (if callback server isn't used). Paste the code from the redirect URL."""
    config = auth.get_config()
    tokens = auth.exchange_code(config, code)
    if tokens:
        identity = auth.get_identity(tokens["access_token"])
        return f"Authenticated as {identity['first_name']} {identity['last_name']} ({identity['email']})\nBusiness: {identity['business_name']}\nAccount ID: {identity['account_id']}"
    return "Authentication failed."


@mcp.tool()
@_handle_errors
async def freshbooks_whoami() -> str:
    """Get the current authenticated user's identity, account ID, and business info."""
    identity = await client.whoami()
    return _fmt(identity)


# ─── Invoice Tools ───

@mcp.tool()
@_handle_errors
async def list_invoices(
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    customer_id: int | None = None,
) -> str:
    """List invoices with optional filters. Status: draft, sent, viewed, outstanding, paid."""
    filters = {}
    if status:
        filters["display_status"] = status
    if customer_id:
        filters["customerid"] = customer_id
    result = await client.accounting_list(
        "invoices/invoices", page, per_page, filters, includes=["lines"]
    )
    return _summarize_list(result, "invoices", ["id", "invoice_number", "display_status", "amount", "outstanding", "customerid", "due_date"])


@mcp.tool()
@_handle_errors
async def get_invoice(invoice_id: int) -> str:
    """Get full details of a specific invoice including line items."""
    result = await client.accounting_get("invoices/invoices", invoice_id)
    return _fmt(result.get("invoice", result))


@mcp.tool()
@_handle_errors
async def create_invoice(
    customer_id: int,
    lines: list[dict],
    due_offset_days: int = 30,
    currency_code: str = "USD",
    notes: str = "",
    po_number: str = "",
) -> str:
    """Create a new invoice. Lines format: [{"name": "Service", "description": "...", "qty": 1, "unit_cost": {"amount": "100.00", "code": "USD"}}]"""
    data = {
        "customerid": customer_id,
        "create_date": _today(),
        "due_offset_days": due_offset_days,
        "currency_code": currency_code,
        "lines": lines,
    }
    if notes:
        data["notes"] = notes
    if po_number:
        data["po_number"] = po_number
    result = await client.accounting_create("invoices/invoices", "invoice", data)
    inv = result.get("invoice", result)
    return f"Invoice #{inv.get('invoice_number', '?')} created (ID: {inv.get('id')}). Amount: ${inv.get('amount', {}).get('amount', '0')}"


@mcp.tool()
@_handle_errors
async def update_invoice(invoice_id: int, updates: dict) -> str:
    """Update an invoice. Pass any writable invoice fields as updates dict."""
    result = await client.accounting_update("invoices/invoices", invoice_id, "invoice", updates)
    inv = result.get("invoice", result)
    return f"Invoice #{inv.get('invoice_number', '?')} updated."


@mcp.tool()
@_handle_errors
async def send_invoice(invoice_id: int) -> str:
    """Send an invoice by email to the client."""
    result = await client.accounting_update(
        "invoices/invoices", invoice_id, "invoice",
        {"action_email": True}
    )
    inv = result.get("invoice", result)
    return f"Invoice #{inv.get('invoice_number', '?')} sent to client."


@mcp.tool()
@_handle_errors
async def delete_invoice(invoice_id: int) -> str:
    """Delete an invoice permanently."""
    await client.accounting_delete("invoices/invoices", invoice_id)
    return f"Invoice {invoice_id} deleted."


# ─── Client Tools ───

@mcp.tool()
@_handle_errors
async def list_clients(
    page: int = 1,
    per_page: int = 25,
    search: str | None = None,
) -> str:
    """List clients. Optional search by name or organization."""
    filters = {}
    if search:
        filters["organization_like"] = search
    result = await client.accounting_list("users/clients", page, per_page, filters)
    return _summarize_list(result, "clients", ["id", "fname", "lname", "organization", "email"])


@mcp.tool()
@_handle_errors
async def get_client(client_id: int) -> str:
    """Get full details of a specific client."""
    result = await client.accounting_get("users/clients", client_id)
    return _fmt(result.get("client", result))


@mcp.tool()
@_handle_errors
async def create_client(
    email: str,
    first_name: str = "",
    last_name: str = "",
    organization: str = "",
    phone: str = "",
    currency_code: str = "USD",
) -> str:
    """Create a new client."""
    data = {"email": email, "currency_code": currency_code}
    if first_name:
        data["fname"] = first_name
    if last_name:
        data["lname"] = last_name
    if organization:
        data["organization"] = organization
    if phone:
        data["mob_phone"] = phone
    result = await client.accounting_create("users/clients", "client", data)
    c = result.get("client", result)
    return f"Client created: {c.get('fname', '')} {c.get('lname', '')} (ID: {c.get('id')})"


@mcp.tool()
@_handle_errors
async def update_client(client_id: int, updates: dict) -> str:
    """Update a client. Pass any writable client fields."""
    result = await client.accounting_update("users/clients", client_id, "client", updates)
    c = result.get("client", result)
    return f"Client {c.get('id')} updated."


# ─── Expense Tools ───

@mcp.tool()
@_handle_errors
async def list_expenses(
    page: int = 1,
    per_page: int = 25,
    client_id: int | None = None,
) -> str:
    """List expenses with optional client filter."""
    filters = {}
    if client_id:
        filters["clientid"] = client_id
    result = await client.accounting_list("expenses/expenses", page, per_page, filters)
    return _summarize_list(result, "expenses", ["id", "vendor", "amount", "date", "status", "categoryid"])


@mcp.tool()
@_handle_errors
async def get_expense(expense_id: int) -> str:
    """Get full details of a specific expense."""
    result = await client.accounting_get("expenses/expenses", expense_id)
    return _fmt(result.get("expense", result))


@mcp.tool()
@_handle_errors
async def create_expense(
    category_id: int,
    staff_id: int,
    amount: str,
    date: str,
    vendor: str = "",
    notes: str = "",
    currency_code: str = "USD",
    client_id: int | None = None,
) -> str:
    """Create a new expense. Amount as string (e.g. '150.00'). Date as YYYY-MM-DD."""
    data = {
        "categoryid": category_id,
        "staffid": staff_id,
        "amount": {"amount": amount, "code": currency_code},
        "date": date,
    }
    if vendor:
        data["vendor"] = vendor
    if notes:
        data["notes"] = notes
    if client_id:
        data["clientid"] = client_id
    result = await client.accounting_create("expenses/expenses", "expense", data)
    e = result.get("expense", result)
    return f"Expense created (ID: {e.get('id')}). Amount: ${amount}"


# ─── Payment Tools ───

@mcp.tool()
@_handle_errors
async def list_payments(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List all payments."""
    result = await client.accounting_list("payments/payments", page, per_page)
    return _summarize_list(result, "payments", ["id", "invoiceid", "amount", "date", "type"])


@mcp.tool()
@_handle_errors
async def create_payment(
    invoice_id: int,
    amount: str,
    date: str,
    payment_type: str = "Other",
    note: str = "",
    currency_code: str = "USD",
) -> str:
    """Record a payment against an invoice. Amount as string. Date as YYYY-MM-DD. Types: Check, Credit, Cash, Bank Transfer, Credit Card, PayPal, ACH, Other."""
    data = {
        "invoiceid": invoice_id,
        "amount": {"amount": amount, "code": currency_code},
        "date": date,
        "type": payment_type,
    }
    if note:
        data["note"] = note
    result = await client.accounting_create("payments/payments", "payment", data)
    p = result.get("payment", result)
    return f"Payment of ${amount} recorded against invoice {invoice_id} (Payment ID: {p.get('id')})"


# ─── Time Entry Tools ───

@mcp.tool()
@_handle_errors
async def list_time_entries(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List time entries."""
    result = await client.projects_list("time_entries", page, per_page)
    entries = result.get("time_entries", [])
    lines = [f"Found {len(entries)} time entries\n"]
    for e in entries:
        dur = e.get("duration", 0)
        hours = dur // 3600
        mins = (dur % 3600) // 60
        lines.append(
            f"ID: {e.get('id')} | {hours}h{mins}m | "
            f"project: {e.get('project_id', '-')} | "
            f"client: {e.get('client_id', '-')} | "
            f"date: {e.get('started_at', '')[:10]} | "
            f"note: {e.get('note', '')[:50]}"
        )
    return "\n".join(lines)


@mcp.tool()
@_handle_errors
async def create_time_entry(
    started_at: str,
    duration_seconds: int,
    client_id: int | None = None,
    project_id: int | None = None,
    note: str = "",
    billable: bool = True,
) -> str:
    """Create a time entry. started_at as ISO8601 (e.g. '2026-03-20T09:00:00'). Duration in seconds."""
    data = {
        "started_at": started_at,
        "duration": duration_seconds,
        "is_logged": True,
        "billable": billable,
    }
    if client_id:
        data["client_id"] = client_id
    if project_id:
        data["project_id"] = project_id
    if note:
        data["note"] = note
    result = await client.projects_create("time_entries", "time_entry", data)
    te = result.get("time_entry", result)
    hours = duration_seconds // 3600
    mins = (duration_seconds % 3600) // 60
    return f"Time entry created (ID: {te.get('id')}). Duration: {hours}h{mins}m"


# ─── Project Tools ───

@mcp.tool()
@_handle_errors
async def list_projects(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List projects."""
    result = await client.projects_list("projects", page, per_page)
    projects = result.get("projects", [])
    lines = [f"Found {len(projects)} projects\n"]
    for p in projects:
        lines.append(
            f"ID: {p.get('id')} | {p.get('title', 'Untitled')} | "
            f"client: {p.get('client_id', '-')} | "
            f"type: {p.get('project_type', '-')} | "
            f"active: {p.get('active', '-')}"
        )
    return "\n".join(lines)


@mcp.tool()
@_handle_errors
async def create_project(
    title: str,
    client_id: int | None = None,
    project_type: str = "hourly_rate",
    billing_method: str = "project_rate",
    description: str = "",
    budget: float | None = None,
    due_date: str | None = None,
) -> str:
    """Create a project. project_type: hourly_rate or fixed_price. billing_method: business_rate, project_rate, service_rate, team_member_rate."""
    data = {
        "title": title,
        "project_type": project_type,
        "billing_method": billing_method,
    }
    if client_id:
        data["client_id"] = client_id
    if description:
        data["description"] = description
    if budget is not None:
        data["budget"] = budget
    if due_date:
        data["due_date"] = due_date
    result = await client.projects_create("projects", "project", data)
    p = result.get("project", result)
    return f"Project '{title}' created (ID: {p.get('id')})"


# ─── Estimate Tools ───

@mcp.tool()
@_handle_errors
async def list_estimates(
    page: int = 1,
    per_page: int = 25,
) -> str:
    """List estimates."""
    result = await client.accounting_list("estimates/estimates", page, per_page)
    return _summarize_list(result, "estimates", ["id", "estimate_number", "display_status", "amount", "customerid"])


@mcp.tool()
@_handle_errors
async def create_estimate(
    customer_id: int,
    lines: list[dict],
    currency_code: str = "USD",
    notes: str = "",
) -> str:
    """Create an estimate. Lines format same as invoices."""
    data = {
        "customerid": customer_id,
        "create_date": _today(),
        "currency_code": currency_code,
        "lines": lines,
    }
    if notes:
        data["notes"] = notes
    result = await client.accounting_create("estimates/estimates", "estimate", data)
    est = result.get("estimate", result)
    return f"Estimate #{est.get('estimate_number', '?')} created (ID: {est.get('id')})"


# ─── Report Tools ───

@mcp.tool()
@_handle_errors
async def get_report(
    report_type: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Get a financial report. Types: profitloss_entity, taxsummary, payments_collected. Dates as YYYY-MM-DD."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    result = await client.get_report(report_type, params)
    return _fmt(result)


# ─── Helpers ───

def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
