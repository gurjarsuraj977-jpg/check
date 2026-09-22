import pytest
from app.batches.service import validate_batch_size

def test_batch_limit():
    validate_batch_size(["x"] * 100)

def test_batch_over_limit():
    with pytest.raises(ValueError):
        validate_batch_size(["x"] * 101)
