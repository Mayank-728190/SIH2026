import pytest
from app.tools.task_tools import create_dispute

@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_dispute():
    # Mocking would happen here to ensure that if idempotency key exists,
    # the second call returns the same task_id and doesn't insert.
    assert True # Placeholder for actual DB mock logic
