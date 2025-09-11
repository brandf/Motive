import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, strategies as st

from motive.action_parser import parse_player_response
from motive.config import ActionConfig, ParameterConfig


@given(
    st.lists(
        st.tuples(
            st.sampled_from(["look", "say", "read"]),
            st.text(min_size=0, max_size=30),
        ),
        min_size=1,
        max_size=5,
    )
)
def test_parser_never_raises_and_returns_structured_actions(actions):
    sample_actions = {
        "look": ActionConfig(id="look", name="look", cost=1, description="", parameters=[], requirements=[], effects=[]),
        "say": ActionConfig(id="say", name="say", cost=1, description="", parameters=[ParameterConfig(name="phrase", type="string", description="")], requirements=[], effects=[]),
        "read": ActionConfig(id="read", name="read", cost=1, description="", parameters=[ParameterConfig(name="object_name", type="string", description="")], requirements=[], effects=[]),
    }

    # Build a response string
    lines = []
    for name, arg in actions:
        if name == "look":
            lines.append("> look")
        elif name == "say":
            lines.append(f"> say '{arg.replace("'", '')}'")
        elif name == "read":
            lines.append(f"> read {arg}")
    response = "\n".join(lines)

    parsed_actions, invalid = parse_player_response(response, sample_actions)

    # Basic sanity checks
    assert isinstance(parsed_actions, list)
    assert isinstance(invalid, list)

