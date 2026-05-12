import httpx
import pytest
import respx

from app.services import scryfall


@pytest.mark.asyncio
@respx.mock(base_url="https://api.scryfall.test")
async def test_search_normalizes_envelope(respx_mock):
    respx_mock.get("/cards/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_cards": 1,
                "has_more": False,
                "data": [
                    {
                        "id": "abc",
                        "name": "Sol Ring",
                        "type_line": "Artifact",
                        "oracle_text": "{T}: Add {C}{C}.",
                        "color_identity": [],
                    }
                ],
            },
        )
    )
    result = await scryfall.search("t:artifact sol ring")
    assert result.total_cards == 1
    assert result.data[0].name == "Sol Ring"


@pytest.mark.asyncio
@respx.mock(base_url="https://api.scryfall.test")
async def test_search_404_returns_empty(respx_mock):
    respx_mock.get("/cards/search").mock(
        return_value=httpx.Response(
            404, json={"object": "error", "details": "Your query didn’t match"}
        )
    )
    result = await scryfall.search("c:purple t:wizard")
    assert result.total_cards == 0
    assert result.data == []


@pytest.mark.asyncio
@respx.mock(base_url="https://api.scryfall.test")
async def test_search_raises_on_5xx(respx_mock):
    respx_mock.get("/cards/search").mock(return_value=httpx.Response(503, text="boom"))
    with pytest.raises(scryfall.ScryfallError):
        await scryfall.search("anything")
