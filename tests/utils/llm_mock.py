from contextlib import contextmanager
from unittest.mock import patch, MagicMock


@contextmanager
def llm_script(scripts_by_player_name: dict[str, str], default: str = "> pass", manual: str = "Test Manual"):
    async def fake_get_response_and_update_history(self, messages_for_llm):
        content = scripts_by_player_name.get(self.name, default)
        return type("_AI", (), {"content": content})()

    with (
        patch("motive.player.create_llm_client", return_value=MagicMock()),
        patch("motive.player.Player.get_response_and_update_history", new=fake_get_response_and_update_history),
        patch("motive.game_master.GameMaster._load_manual_content", return_value=manual),
    ):
        yield


