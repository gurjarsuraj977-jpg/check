from app.security import fingerprint, encrypt, decrypt

def test_fingerprint_is_stable_and_secret_independent():
    assert fingerprint("x") == fingerprint("x")
    assert fingerprint("x") != fingerprint("y")

def test_encryption_roundtrip():
    value = "TEST_FIXTURE_VALID:123"
    assert decrypt(encrypt(value)) == value
