import asyncio
import pytest
from app.workers.adapter import SandboxFixtureAdapter

@pytest.mark.asyncio
async def test_sandbox_fixture_adapter():
    adapter = SandboxFixtureAdapter()
    assert (await adapter.verify("TEST_FIXTURE_VALID:1")).status == "sandbox_valid"
    assert (await adapter.verify("TEST_FIXTURE_INVALID:1")).status == "sandbox_invalid"
    assert (await adapter.verify("anything")).status == "unsupported_fixture"
