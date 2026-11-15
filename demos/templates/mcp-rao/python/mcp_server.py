"""Cartwright Freight Group - MCP surface for UC02 Rate Integrity.

ARAG's own Retrieval Agent is the MCP client here, not this app - the agent
plans, calls this server's two read-only tools and reconciles them:
  - list_invoices     - the OpenEdge rating/tariff data (what was BILLED)
  - get_contracted_rate - what was AGREED, per customer/lane
This app never runs its own planner against /mcp; it only exposes it
(rao-workflow skill).

Known platform gap, disclosed not hidden (found live building this, 20 Aug
2026): the agent-side "ask" context module (a driver-based cross-KB
retrieval node, provider "nucliadb") could not be made to authenticate
against the Cartwright Freight Group contract KB via any api_key/manager field
combination tried - every attempt came back "No roles could be resolved
for AnonymousUser", meaning the credential never actually reached the
downstream KB call. Rather than keep guessing at an undocumented field
name, the "what was contracted" side is exposed as a SECOND MCP tool
instead: get_contracted_rate() calls this app's own arag.ask() - the
exact same, already-proven ARAG /ask call UC01 uses - against the real
contract Knowledge Box, and returns the grounded, cited answer text. This
is still a genuine ARAG call end to end (retrieval + generation both run
on the platform); only the ROUTE from the Retrieval Agent to that call
changed from a direct KB-driver context node to an MCP tool. See the
solution-architecture reveal on /rate-integrity for the honest version of
this story.

Auth: every tool call requires this app's own bearer token
(APP_MCP_TOKEN, set server-side and forwarded by the agent's MCP driver
config) - an unauthenticated call 401s. This is a single shared service
credential, not per-user RBAC (Cartwright Freight Group has no login/session layer
in this build), disclosed honestly rather than claimed as more than it is.

Endpoint: POST /mcp, JSON-RPC 2.0, Streamable HTTP, stateless.
"""
import json
import re
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import arag
import billing
from arag import ENV

APP_MCP_TOKEN = ENV.get("APP_MCP_TOKEN", "cartwright-freight-mcp-demo-token")

# ARAG namespaces tool names with a trailing agent-uuid suffix
# (e.g. list_invoices__2f527fa6-...) - strip it before matching.
_UUID_SUFFIX = re.compile(
    r"__[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def strip_agent_suffix(name: str) -> str:
    return _UUID_SUFFIX.sub("", name)


TOOLS = [
    {
        "name": "list_invoices",
        "description": ("Read-only lookup of recent Cartwright Freight Group freight invoices, "
                        "with the base rate and fuel-surcharge percentage actually "
                        "billed on each line - the OpenEdge rating/tariff data. "
                        "Optionally filter by customer slug (e.g. 'harrow-retail', "
                        "'bluewater-foods', 'anvil-construction', 'coastal-pharma', "
                        "'ironbark-mining')."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer": {"type": "string",
                            "description": "Customer slug to filter by, or omit for all customers."},
            },
        },
    },
    {
        "name": "get_contracted_rate",
        "description": ("Read-only lookup of the CONTRACTED base rate and terms for a "
                        "Cartwright Freight Group customer and lane, grounded against the real "
                        "signed contract and rate schedule documents. Use this to find "
                        "what was actually AGREED, to compare against what was billed."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string",
                                  "description": "The customer's full name, e.g. 'Harrow Retail Group'."},
                "lane": {"type": "string",
                        "description": "The lane, e.g. 'Sydney DC to Brisbane DC'."},
            },
            "required": ["customer_name", "lane"],
        },
    },
]


async def dispatch(name: str, arguments: dict) -> Any:
    tool = strip_agent_suffix(name)
    if tool == "list_invoices":
        return billing.list_invoices(customer=arguments.get("customer"))
    if tool == "get_contracted_rate":
        customer_name = arguments.get("customer_name", "")
        lane = arguments.get("lane", "")
        result = await arag.ask(
            f"What is the contracted base rate for {customer_name} on the {lane} lane, "
            f"and what is the fuel surcharge escalation schedule?")
        return {"answer": result["answer"], "grounded": result["grounded"]}
    raise ValueError(f"Unknown tool: {name}")


router = APIRouter()


@router.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {APP_MCP_TOKEN}":
        return JSONResponse({"jsonrpc": "2.0", "id": None,
                             "error": {"code": -32001, "message": "Unauthorized"}},
                            status_code=401)

    body = await request.json()
    method = body.get("method")
    req_id = body.get("id")

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = body.get("params") or {}
        name = params.get("name", "")
        arguments = params.get("arguments") or {}
        try:
            result = await dispatch(name, arguments)
        except ValueError as e:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32601, "message": str(e)}}
        return {"jsonrpc": "2.0", "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}

    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def mount(app):
    app.include_router(router)
