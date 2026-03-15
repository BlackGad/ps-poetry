import os
from unittest.mock import patch

from ps.plugin.module.delivery.token_resolvers._env_resolver import EnvResolver


def test_env_no_args_returns_none():
    assert EnvResolver()([]) is None


def test_env_returns_value_when_var_set():
    with patch.dict(os.environ, {"MY_VAR": "hello"}):
        assert EnvResolver()(["MY_VAR"]) == "hello"


def test_env_returns_none_when_var_missing():
    env = {k: v for k, v in os.environ.items() if k != "MY_VAR"}
    with patch.dict(os.environ, env, clear=True):
        assert EnvResolver()(["MY_VAR"]) is None


def test_env_returns_empty_string_when_var_is_empty():
    with patch.dict(os.environ, {"MY_VAR": ""}):
        assert EnvResolver()(["MY_VAR"]) == ""


def test_env_ignores_extra_args():
    with patch.dict(os.environ, {"MY_VAR": "42"}):
        assert EnvResolver()(["MY_VAR", "ignored"]) == "42"
