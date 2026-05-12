from app.models.chat import ChatMessage
from app.services import guardrails


def _msg(text: str) -> list[ChatMessage]:
    return [ChatMessage(role="user", content=text)]


def test_allows_on_topic_message():
    assert guardrails.check_inbound(_msg("Show me blue draw spells in Commander")) is None


def test_blocks_medical_advice():
    refusal = guardrails.check_inbound(_msg("What dosage of ibuprofen is safe?"))
    assert refusal is not None
    assert "Magic" in refusal


def test_blocks_relationship_attempt():
    refusal = guardrails.check_inbound(_msg("Will you be my girlfriend?"))
    assert refusal is not None


def test_mtg_terms_override_false_positive():
    # "tax" appears in our finance pattern; but if the prompt is clearly MTG
    # we should let it through (e.g. "Smothering Tithe tax")
    assert (
        guardrails.check_inbound(
            _msg("Does Smothering Tithe count as a tax effect for my Commander deck?")
        )
        is None
    )


def test_empty_messages_returns_none():
    assert guardrails.check_inbound([]) is None
