#!/usr/bin/env python3
"""Test the rainmaker-http client against the real RainMaker API (GETs only).

This script uses credentials present in the notebook you provided.
It prints a redacted summary: node count, node ids and names, and a
sample of parameter keys for the first node.

DO NOT commit this file if you replace the credentials with real secrets.
"""
import asyncio
from rainmaker_http import RainmakerClient

import os

HOST = "https://api.rainmaker.espressif.com/v1/"
# Credentials must be provided via environment variables to avoid
# embedding secrets in the repository. Set `RAINMAKER_USERNAME` and
# `RAINMAKER_PASSWORD` in your shell before running this script.
USERNAME = os.environ.get("RAINMAKER_USERNAME")
PASSWORD = os.environ.get("RAINMAKER_PASSWORD")

async def main() -> None:
    if not USERNAME or not PASSWORD:
        print(
            "Credentials not provided. Set RAINMAKER_USERNAME and RAINMAKER_PASSWORD environment variables."
        )
        return

    async with RainmakerClient(HOST) as client:
        try:
            await client.async_login(USERNAME, PASSWORD)
        except Exception as err:
            print("Login failed:", type(err).__name__, str(err))
            return

        try:
            nodes = await client.async_get_nodes()
        except Exception as err:
            print("Failed to fetch nodes:", type(err).__name__, str(err))
            return

        # Normalize node list
        node_items = []
        if isinstance(nodes, dict):
            if "nodes" in nodes and isinstance(nodes["nodes"], (list, dict)):
                node_items = nodes["nodes"] if isinstance(nodes["nodes"], list) else list(nodes["nodes"].values())
            else:
                node_items = list(nodes.values()) if nodes else []
        elif isinstance(nodes, list):
            node_items = nodes

        print(f"Found {len(node_items)} nodes")
        for n in node_items[:20]:
            if isinstance(n, dict):
                nodeid = n.get("nodeid") or n.get("id") or n.get("node_id") or "<unknown>"
                name = n.get("name") or n.get("Name") or ""
            else:
                nodeid = str(n)
                name = ""
            print(f"- {nodeid} (name: {name})")

        if not node_items:
            return

        # Fetch params for first node (GET only)
        first = node_items[0]
        first_id = first.get("nodeid") if isinstance(first, dict) else str(first)
        try:
            params = await client.async_get_params(first_id)
        except Exception as err:
            print("Failed to fetch params for node:", first_id, type(err).__name__, str(err))
            return

        # Unwrap single-wrapper payloads
        param_keys = []
        if isinstance(params, dict):
            if len(params) == 1:
                inner = next(iter(params.values()))
                if isinstance(inner, dict):
                    param_keys = list(inner.keys())[:50]
            else:
                param_keys = list(params.keys())[:50]

        print(f"Sample param keys for node {first_id}: {param_keys}")

if __name__ == "__main__":
    asyncio.run(main())
