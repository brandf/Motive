#!/usr/bin/env python3
import pytest

from motive.hooks.core_hooks import calculate_help_cost


def test_help_cost_general_dict_config():
    action_config = {
        'name': 'help',
        'cost': {
            'type': 'code_binding',
            'function_name': 'calculate_help_cost',
            'value': 1,
        },
    }
    cost = calculate_help_cost(None, None, action_config, {})
    assert cost == 1


def test_help_cost_with_category_halves_cost():
    action_config = {
        'name': 'help',
        'cost': {
            'type': 'code_binding',
            'function_name': 'calculate_help_cost',
            'value': 1,
        },
    }
    cost = calculate_help_cost(None, None, action_config, {"category": "communication"})
    assert cost == 0


