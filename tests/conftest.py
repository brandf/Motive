import pytest


LEGACY_XFAIL_PREFIXES = (
    # Intentionally left mostly empty; we are removing legacy tests as we migrate
)


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        path_str = str(item.fspath)
        # Normalize to forward slashes for cross-platform matching
        norm_path = path_str.replace('\\', '/')
        if any(norm_path.endswith(prefix) or norm_path.startswith(prefix) or (prefix in norm_path) for prefix in LEGACY_XFAIL_PREFIXES):
            item.add_marker(pytest.mark.xfail(reason="Legacy/migration-era test pending v2 minimal replacement", strict=False))

import os


def normalize_text(s: str) -> str:
    # Collapse multiple spaces/newlines and strip
    return " ".join(s.split())


def pytest_configure(config):
    # Disable file logging during tests by default
    os.environ.setdefault("MOTIVE_DISABLE_FILE_LOGGING", "1")


