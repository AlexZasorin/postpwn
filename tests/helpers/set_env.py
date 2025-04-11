from contextlib import contextmanager
import os


@contextmanager
def set_env(env_vars: dict[str, str]):
    original_env: dict[str, str | None] = {}
    try:
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key, value in original_env.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value
