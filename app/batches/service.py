MAX_BATCH_SIZE = 100

def validate_batch_size(items: list[str]) -> None:
    if not items:
        raise ValueError("Batch is empty")
    if len(items) > MAX_BATCH_SIZE:
        raise ValueError(f"Batch cannot exceed {MAX_BATCH_SIZE} records")
