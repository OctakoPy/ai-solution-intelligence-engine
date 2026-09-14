"""Shared test fixtures."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run async tests on the asyncio backend only (trio is not installed)."""
    return "asyncio"
