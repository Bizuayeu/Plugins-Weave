"""Stage 2: UseCase port contracts (Protocol + runtime_checkable).

Mirrors EmailingEssay's usecases/ports.py style. Verifies the abstract shapes
the SKILL.md procedure (Infrastructure) will implement, and the key security
contract: SecretProviderPort hands a token to a callback then drops it.
"""
from usecases.ports import (
    FaceUiPort,
    MemoryLoaderPort,
    SecretProviderPort,
    VcsPort,
)


class TestPortShapes:
    def test_memory_loader_has_load_public(self):
        assert hasattr(MemoryLoaderPort, "load_public")

    def test_secret_provider_has_with_token(self):
        assert hasattr(SecretProviderPort, "with_token")

    def test_vcs_has_push_and_pr(self):
        assert hasattr(VcsPort, "push_branch")
        assert hasattr(VcsPort, "open_pr")

    def test_face_ui_has_boot(self):
        assert hasattr(FaceUiPort, "boot")


class TestRuntimeCheckable:
    def test_fake_loader_satisfies_protocol(self):
        class FakeLoader:
            def load_public(self, repo, files):
                return {}

        assert isinstance(FakeLoader(), MemoryLoaderPort)

    def test_fake_face_satisfies_protocol(self):
        class FakeFace:
            def boot(self):
                return None

        assert isinstance(FakeFace(), FaceUiPort)


class TestSecretProviderContract:
    """The whole point of with_token: the token must not outlive the callback."""

    def test_with_token_passes_token_then_releases(self):
        class FakeSecret:
            def __init__(self, token):
                self._token = token
                self.released = False

            def with_token(self, scope, fn):
                try:
                    return fn(self._token)
                finally:
                    self._token = None
                    self.released = True

        fake = FakeSecret("ghp_dummy_secret")
        seen = {}
        result = fake.with_token("contents:read", lambda t: seen.update(tok=t) or "ok")

        assert result == "ok"
        assert seen["tok"] == "ghp_dummy_secret"  # callback saw the token
        assert fake.released is True               # ...and it was released after
        assert fake._token is None

    def test_fake_secret_satisfies_protocol(self):
        class FakeSecret:
            def with_token(self, scope, fn):
                return fn("x")

        assert isinstance(FakeSecret(), SecretProviderPort)
