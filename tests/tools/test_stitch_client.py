import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_init_raises_without_api_key():
    with patch.dict("os.environ", {}, clear=True):
        from importlib import reload
        import tools.stitch_client as m
        reload(m)
        with pytest.raises(ValueError, match="STITCH_API_KEY"):
            m.StitchMCPClient()


def test_init_reads_env_var():
    with patch.dict("os.environ", {"STITCH_API_KEY": "test-key"}):
        from importlib import reload
        import tools.stitch_client as m
        reload(m)
        client = m.StitchMCPClient()
        assert client.api_key == "test-key"


def test_init_accepts_explicit_key():
    client_module = _import_client()
    client = client_module.StitchMCPClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


@pytest.mark.asyncio
async def test_request_returns_empty_dict_on_http_error():
    client = _import_client().StitchMCPClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        result = await client._request("tools/list", {})
        assert result == {}


@pytest.mark.asyncio
async def test_request_returns_json_on_success():
    client = _import_client().StitchMCPClient(api_key="test-key")
    expected = {"result": {"tools": []}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        result = await client._request("tools/list", {})
        assert result == expected


@pytest.mark.asyncio
async def test_request_returns_empty_on_exception():
    client = _import_client().StitchMCPClient(api_key="test-key")

    with patch("httpx.AsyncClient") as mock_cls:
        mock_cls.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        result = await client._request("tools/list", {})
        assert result == {}


def _import_client():
    from importlib import reload
    import tools.stitch_client as m
    reload(m)
    return m
