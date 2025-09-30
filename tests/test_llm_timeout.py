import asyncio
import pytest
from langchain_core.messages import HumanMessage

from motive import llm_factory
from motive.player import Player


class _SlowLLM:
    async def ainvoke(self, messages, **kwargs):
        await asyncio.sleep(0.05)
        return None


@pytest.mark.asyncio
async def test_rate_limited_request_times_out(monkeypatch):
    provider = "timeout_provider"
    monkeypatch.setitem(
        llm_factory.RATE_LIMIT_CONFIG,
        provider,
        {
            "requests_per_minute": 1000,
            "requests_per_hour": 1000,
            "max_retries": 0,
            "retry_delay": 0.0,
            "backoff_multiplier": 1.0,
            "request_timeout": 0.01,
        },
    )
    # Reset any cached rate limit state for the provider
    for state in llm_factory._rate_limit_state.values():
        state.pop(provider, None)

    with pytest.raises(TimeoutError):
        await llm_factory._rate_limited_request(
            provider,
            _SlowLLM(),
            messages=[HumanMessage(content="> look")],
            timeout=0.01,
        )


class _FlakyLLM:
    def __init__(self):
        self.calls = 0

    async def ainvoke(self, messages, **kwargs):
        self.calls += 1
        if self.calls < 3:
            raise TimeoutError("Request timed out after 1.0s")
        mock_response = type("Resp", (), {"content": "> pass"})()
        return mock_response


@pytest.mark.asyncio
async def test_player_retries_on_timeout(tmp_path):
    player = Player(
        name="TestPlayer",
        provider="dummy",
        model="dummy",
        log_dir=str(tmp_path),
        no_file_logging=True,
    )
    player.llm_client = _FlakyLLM()

    response = await player.get_response_and_update_history(
        [HumanMessage(content="> look")]
    )

    assert response.content == "> pass"
    assert player.llm_client.calls == 3
