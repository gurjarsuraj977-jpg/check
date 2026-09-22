from app.auth.service import hash_password, verify_password

def test_password_hash_roundtrip():
    password = "example-only-password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)
