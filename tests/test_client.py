import pytest

from rainmaker_http.client import RainmakerClient
from rainmaker_http.exceptions import RainmakerAuthError


class DummyResp:
    def __init__(self, status=200, json_data=None, text_data=""):
        self.status = status
        self._json = json_data
        self._text = text_data

    async def text(self):
        return self._text

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


class DummySession:
    def __init__(self, responses):
        self._responses = responses

    async def post(self, url, json=None, headers=None, timeout=None):
        return DummyResp(json_data=self._responses.get("login"))

    async def get(self, url, headers=None, params=None, timeout=None):
        # inspect path to choose response
        if "user/nodes" in url:
            return DummyResp(json_data=self._responses.get("nodes"))
        if "user/nodes/params" in url:
            return DummyResp(json_data=self._responses.get("params"))
        if "user/nodes/config" in url:
            return DummyResp(json_data=self._responses.get("config"))
        return DummyResp(json_data=None)

    async def put(self, url, headers=None, json=None, timeout=None):
        return DummyResp(json_data=self._responses.get("set"))

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_login_and_get_nodes():
    responses = {
        "login": {"status": "success", "accesstoken": "tok"},
        "nodes": [{"nodeid": "n1", "name": "Device 1"}],
    }
    session = DummySession(responses)
    client = RainmakerClient("https://example.local/", session=session)
    await client.async_login("u", "p")
    nodes = await client.async_get_nodes()
    assert isinstance(nodes, list)
    assert nodes[0]["nodeid"] == "n1"


@pytest.mark.asyncio
async def test_login_invalid():
    responses = {"login": {"status": "fail"}}
    session = DummySession(responses)
    client = RainmakerClient("https://example.local/", session=session)
    with pytest.raises(RainmakerAuthError):
        await client.async_login("u", "p")
