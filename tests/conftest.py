import os


def normalize_text(s: str) -> str:
    # Collapse multiple spaces/newlines and strip
    return " ".join(s.split())


def pytest_configure(config):
    # Disable file logging during tests by default
    os.environ.setdefault("MOTIVE_DISABLE_FILE_LOGGING", "1")


