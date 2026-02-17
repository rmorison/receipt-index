"""Tests for receipt_index.extraction."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

from receipt_index.extraction import _build_prompt, _strip_html_tags, extract_metadata
from receipt_index.models import RawReceipt, ReceiptMetadata


class TestBuildPrompt:
    """Tests for _build_prompt."""

    def test_includes_subject_sender_date(self, sample_raw_receipt: RawReceipt) -> None:
        prompt = _build_prompt(sample_raw_receipt)
        assert "Subject: Your Amazon.com order" in prompt
        assert "From: no-reply@amazon.com" in prompt
        assert "2025-06-15" in prompt

    def test_uses_text_body(self, sample_raw_receipt: RawReceipt) -> None:
        prompt = _build_prompt(sample_raw_receipt)
        assert "Order Total: $42.99" in prompt
        assert "Item: Python Cookbook" in prompt

    def test_strips_html_when_no_text_body(self) -> None:
        raw = RawReceipt(
            source_id="test",
            subject="HTML Receipt",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            html_body="<p>Your total is <strong>$99.00</strong></p>",
        )
        prompt = _build_prompt(raw)
        assert "Your total is $99.00" in prompt
        assert "<p>" not in prompt
        assert "<strong>" not in prompt

    def test_prefers_text_over_html(self) -> None:
        raw = RawReceipt(
            source_id="test",
            subject="Both",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            text_body="Text version",
            html_body="<p>HTML version</p>",
        )
        prompt = _build_prompt(raw)
        assert "Text version" in prompt
        assert "HTML version" not in prompt

    def test_handles_no_body(self) -> None:
        raw = RawReceipt(
            source_id="test",
            subject="Empty",
            sender="x@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
        )
        prompt = _build_prompt(raw)
        assert "(no body content)" in prompt


class TestStripHtmlTags:
    """Tests for _strip_html_tags."""

    def test_simple_tags(self) -> None:
        assert _strip_html_tags("<p>Hello</p>") == "Hello"

    def test_nested_tags(self) -> None:
        result = _strip_html_tags("<div><p>Nested <em>text</em></p></div>")
        assert result == "Nested text"

    def test_empty_string(self) -> None:
        assert _strip_html_tags("") == ""

    def test_no_tags(self) -> None:
        assert _strip_html_tags("Plain text") == "Plain text"

    def test_preserves_entity_refs(self) -> None:
        result = _strip_html_tags("<p>Price &amp; tax</p>")
        assert "Price" in result
        assert "tax" in result

    def test_attributes_stripped(self) -> None:
        result = _strip_html_tags('<a href="http://example.com">Link</a>')
        assert result == "Link"
        assert "href" not in result


class TestExtractMetadata:
    """Tests for extract_metadata."""

    def test_returns_receipt_metadata(self, sample_raw_receipt: RawReceipt) -> None:
        expected = ReceiptMetadata(
            vendor="Amazon",
            amount=Decimal("42.99"),
            date=date(2025, 6, 15),
            confidence=0.95,
        )

        mock_result = MagicMock()
        mock_result.output = expected

        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = mock_result

        result = extract_metadata(sample_raw_receipt, agent=mock_agent)

        assert result == expected
        assert result.vendor == "Amazon"
        assert result.amount == Decimal("42.99")

    def test_passes_prompt_to_agent(self, sample_raw_receipt: RawReceipt) -> None:
        mock_result = MagicMock()
        mock_result.output = ReceiptMetadata(
            vendor="Amazon",
            amount=Decimal("42.99"),
            date=date(2025, 6, 15),
            confidence=0.95,
        )

        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = mock_result

        extract_metadata(sample_raw_receipt, agent=mock_agent)

        call_args = mock_agent.run_sync.call_args
        prompt = call_args[0][0]
        assert "Subject: Your Amazon.com order" in prompt
        assert "Order Total: $42.99" in prompt

    def test_uses_injected_agent(self, sample_raw_receipt: RawReceipt) -> None:
        mock_result = MagicMock()
        mock_result.output = ReceiptMetadata(
            vendor="Test",
            amount=Decimal("1.00"),
            date=date(2025, 1, 1),
            confidence=0.5,
        )

        mock_agent = MagicMock()
        mock_agent.run_sync.return_value = mock_result

        extract_metadata(sample_raw_receipt, agent=mock_agent)

        # Agent's run_sync should have been called exactly once
        mock_agent.run_sync.assert_called_once()
