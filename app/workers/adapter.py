"""Safe verification adapter boundary.

Production integrations must implement this interface against an explicitly
authorized sandbox/test environment. This project deliberately ships only a
synthetic fixture adapter; it never calls Stripe or validates live secrets.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class VerificationResult:
    status: str
    detail: str = ""

class VerificationAdapter:
    async def verify(self, secret: str) -> VerificationResult:
        raise NotImplementedError

class SandboxFixtureAdapter(VerificationAdapter):
    """Synthetic adapter used to exercise worker behavior without external calls.

    Fixtures must be explicitly prefixed so ordinary input is never interpreted
    as a credential for a real service.
    """
    async def verify(self, secret: str) -> VerificationResult:
        if secret.startswith("TEST_FIXTURE_VALID:"):
            return VerificationResult("sandbox_valid", "synthetic fixture")
        if secret.startswith("TEST_FIXTURE_INVALID:"):
            return VerificationResult("sandbox_invalid", "synthetic fixture")
        return VerificationResult("unsupported_fixture", "not a sandbox fixture")
