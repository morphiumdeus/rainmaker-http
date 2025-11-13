# rainmaker-http

Minimal async HTTP client for ESP RainMaker (Zehnder Multi Controller).

This package provides a small, dependency-light `aiohttp` client that
implements the HTTP endpoints used by the RainMaker ecosystem. It is
intended to be a minimal alternative to large upstream SDKs when an
integration wants to avoid heavy dependencies.

Install (dev):

```bash
pip install -e .[dev]
```

Quick usage:

```python
import asyncio
from rainmaker_http import RainmakerClient

async def main():
    async with RainmakerClient("https://api.rainmaker.example/") as client:
        await client.async_login("username", "password")
        nodes = await client.async_get_nodes()
        print(nodes)

asyncio.run(main())
```

Publishing
----------

Build and upload:

```bash
python -m build
python -m twine upload dist/*
```

Test script
-----------

The repository includes a small test script `scripts/test_real_api.py` that exercises GET-only endpoints.
Do NOT store credentials in the file. Provide credentials via environment variables:

```bash
export RAINMAKER_USERNAME="your-username"
export RAINMAKER_PASSWORD="your-password"
PYTHONPATH=$(pwd) python scripts/test_real_api.py
```

CI / Publishing
----------------

This repo includes a GitHub Actions workflow to build and publish the package when creating a release. The workflow expects the `PYPI_API_TOKEN` secret to be configured in the repository settings.

See `.github/workflows/publish.yml` for details.
