"""Tests for receipt_index.config."""

from __future__ import annotations

import pytest

from receipt_index.config import (
    ImapConfig,
    get_anthropic_api_key,
    get_imap_config,
    get_llm_model,
)


class TestGetImapConfig:
    """Tests for get_imap_config()."""

    def test_valid_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("IMAP_HOST", "mail.example.com")
        monkeypatch.setenv("IMAP_USERNAME", "user@example.com")
        monkeypatch.setenv("IMAP_PASSWORD", "pass123")  # pragma: allowlist secret

        config = get_imap_config()

        assert config.host == "mail.example.com"
        assert config.username == "user@example.com"
        assert config.password == "pass123"  # pragma: allowlist secret
        assert config.port == 993
        assert config.folder == "INBOX"

    def test_custom_port_and_folder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("IMAP_HOST", "mail.example.com")
        monkeypatch.setenv("IMAP_USERNAME", "user@example.com")
        monkeypatch.setenv("IMAP_PASSWORD", "pass123")  # pragma: allowlist secret
        monkeypatch.setenv("IMAP_PORT", "143")
        monkeypatch.setenv("IMAP_FOLDER", "Receipts")

        config = get_imap_config()

        assert config.port == 143
        assert config.folder == "Receipts"

    def test_missing_host_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("IMAP_HOST", raising=False)
        monkeypatch.setenv("IMAP_USERNAME", "user@example.com")
        monkeypatch.setenv("IMAP_PASSWORD", "pass123")  # pragma: allowlist secret

        with pytest.raises(ValueError, match="IMAP_HOST"):
            get_imap_config()

    def test_missing_username_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("IMAP_HOST", "mail.example.com")
        monkeypatch.delenv("IMAP_USERNAME", raising=False)
        monkeypatch.setenv("IMAP_PASSWORD", "pass123")  # pragma: allowlist secret

        with pytest.raises(ValueError, match="IMAP_USERNAME"):
            get_imap_config()

    def test_missing_password_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("IMAP_HOST", "mail.example.com")
        monkeypatch.setenv("IMAP_USERNAME", "user@example.com")
        monkeypatch.delenv("IMAP_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="IMAP_PASSWORD"):
            get_imap_config()

    def test_missing_all_required_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("IMAP_HOST", raising=False)
        monkeypatch.delenv("IMAP_USERNAME", raising=False)
        monkeypatch.delenv("IMAP_PASSWORD", raising=False)

        with pytest.raises(
            ValueError, match=r"IMAP_HOST.*IMAP_USERNAME.*IMAP_PASSWORD"
        ):
            get_imap_config()

    def test_config_is_frozen(self) -> None:
        config = ImapConfig(
            host="mail.example.com",
            username="user@example.com",
            password="pass",  # pragma: allowlist secret
        )
        with pytest.raises(AttributeError):
            config.host = "other.example.com"  # type: ignore[misc]


class TestGetAnthropicApiKey:
    """Tests for get_anthropic_api_key()."""

    def test_key_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        assert get_anthropic_api_key() == "sk-ant-test-key"

    def test_key_missing_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_anthropic_api_key()


class TestGetLlmModel:
    """Tests for get_llm_model()."""

    def test_default_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLM_MODEL", raising=False)
        assert get_llm_model() == "claude-haiku-4-5-20251001"

    def test_custom_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LLM_MODEL", "claude-sonnet-4-20250514")
        assert get_llm_model() == "claude-sonnet-4-20250514"
