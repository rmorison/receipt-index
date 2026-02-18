"""Tests for receipt_index.renderer."""

from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from receipt_index.models import Attachment, RawReceipt
from receipt_index.renderer import (
    _embed_inline_images,
    _find_pdf_attachment,
    _html_to_pdf_bytes,
    _render_text_to_pdf,
    render_pdf,
)


class TestRenderPdf:
    """Tests for the top-level render_pdf function."""

    def test_pdf_attachment_passthrough(self) -> None:
        pdf_data = b"%PDF-1.4 test content"
        raw = RawReceipt(
            source_id="test",
            subject="Receipt",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            attachments=[
                Attachment(
                    filename="receipt.pdf",
                    content_type="application/pdf",
                    data=pdf_data,
                )
            ],
        )
        result = render_pdf(raw)
        assert result == pdf_data

    @patch("receipt_index.renderer._html_to_pdf_bytes")
    def test_html_body_rendered(self, mock_pdf: pytest.fixture) -> None:
        mock_pdf.return_value = b"pdf-from-html"
        raw = RawReceipt(
            source_id="test",
            subject="HTML Receipt",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            html_body="<p>Your receipt</p>",
        )
        result = render_pdf(raw)
        assert result == b"pdf-from-html"
        mock_pdf.assert_called_once()

    @patch("receipt_index.renderer._html_to_pdf_bytes")
    def test_text_body_rendered(self, mock_pdf: pytest.fixture) -> None:
        mock_pdf.return_value = b"pdf-from-text"
        raw = RawReceipt(
            source_id="test",
            subject="Text Receipt",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            text_body="Your total: $42.99",
        )
        result = render_pdf(raw)
        assert result == b"pdf-from-text"

    @patch("receipt_index.renderer._html_to_pdf_bytes")
    def test_no_body_fallback(self, mock_pdf: pytest.fixture) -> None:
        mock_pdf.return_value = b"pdf-fallback"
        raw = RawReceipt(
            source_id="test",
            subject="Empty",
            sender="x@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
        )
        result = render_pdf(raw)
        assert result == b"pdf-fallback"

    def test_pdf_attachment_preferred_over_html(self) -> None:
        pdf_data = b"%PDF-1.4 original"
        raw = RawReceipt(
            source_id="test",
            subject="Receipt",
            sender="shop@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            html_body="<p>Receipt HTML</p>",
            attachments=[
                Attachment(
                    filename="receipt.pdf",
                    content_type="application/pdf",
                    data=pdf_data,
                )
            ],
        )
        result = render_pdf(raw)
        assert result == pdf_data


class TestFindPdfAttachment:
    """Tests for _find_pdf_attachment."""

    def test_finds_pdf(self) -> None:
        pdf_data = b"%PDF data"
        attachments = [
            Attachment(
                filename="doc.pdf", content_type="application/pdf", data=pdf_data
            )
        ]
        assert _find_pdf_attachment(attachments) == pdf_data

    def test_returns_none_when_no_pdf(self) -> None:
        attachments = [
            Attachment(filename="image.png", content_type="image/png", data=b"png")
        ]
        assert _find_pdf_attachment(attachments) is None

    def test_returns_none_for_empty_list(self) -> None:
        assert _find_pdf_attachment([]) is None

    def test_first_pdf_wins(self) -> None:
        attachments = [
            Attachment(
                filename="first.pdf",
                content_type="application/pdf",
                data=b"first",
            ),
            Attachment(
                filename="second.pdf",
                content_type="application/pdf",
                data=b"second",
            ),
        ]
        assert _find_pdf_attachment(attachments) == b"first"

    def test_ignores_non_pdf(self) -> None:
        attachments = [
            Attachment(filename="img.jpg", content_type="image/jpeg", data=b"jpg"),
            Attachment(filename="doc.pdf", content_type="application/pdf", data=b"pdf"),
        ]
        assert _find_pdf_attachment(attachments) == b"pdf"


class TestEmbedInlineImages:
    """Tests for _embed_inline_images."""

    def test_replaces_cid_reference(self) -> None:
        img_data = b"\x89PNG"
        attachments = [
            Attachment(filename="logo", content_type="image/png", data=img_data)
        ]
        html = '<img src="cid:logo">'
        result = _embed_inline_images(html, attachments)

        expected_b64 = base64.b64encode(img_data).decode("ascii")
        assert f"data:image/png;base64,{expected_b64}" in result
        assert "cid:" not in result

    def test_multiple_images(self) -> None:
        attachments = [
            Attachment(filename="img1", content_type="image/png", data=b"png1"),
            Attachment(filename="img2", content_type="image/jpeg", data=b"jpg2"),
        ]
        html_content = '<img src="cid:img1"><img src="cid:img2">'
        result = _embed_inline_images(html_content, attachments)

        assert "data:image/png;base64," in result
        assert "data:image/jpeg;base64," in result

    def test_no_cid_passthrough(self) -> None:
        html_content = '<img src="https://example.com/img.png">'
        result = _embed_inline_images(html_content, [])
        assert result == html_content

    def test_missing_attachment_keeps_cid(self) -> None:
        html_content = '<img src="cid:missing">'
        attachments = [
            Attachment(filename="other", content_type="image/png", data=b"png")
        ]
        result = _embed_inline_images(html_content, attachments)
        assert "cid:missing" in result

    def test_non_image_attachments_ignored(self) -> None:
        html_content = '<img src="cid:doc">'
        attachments = [
            Attachment(filename="doc", content_type="application/pdf", data=b"pdf")
        ]
        result = _embed_inline_images(html_content, attachments)
        # PDF attachments should not be in the image map
        assert "cid:doc" in result


class TestRenderTextToPdf:
    """Tests for _render_text_to_pdf."""

    @patch("receipt_index.renderer._html_to_pdf_bytes")
    def test_template_includes_subject_and_sender(
        self, mock_pdf: pytest.fixture
    ) -> None:
        mock_pdf.return_value = b"pdf-bytes"
        raw = RawReceipt(
            source_id="test",
            subject="My Receipt",
            sender="shop@example.com",
            date=datetime(2025, 3, 15, tzinfo=UTC),
            text_body="Total: $100",
        )
        _render_text_to_pdf(raw)

        call_args = mock_pdf.call_args[0][0]
        assert "My Receipt" in call_args
        assert "shop@example.com" in call_args
        assert "2025-03-15" in call_args
        assert "Total: $100" in call_args

    @patch("receipt_index.renderer._html_to_pdf_bytes")
    def test_html_escapes_body(self, mock_pdf: pytest.fixture) -> None:
        mock_pdf.return_value = b"pdf-bytes"
        raw = RawReceipt(
            source_id="test",
            subject="Test",
            sender="x@example.com",
            date=datetime(2025, 1, 1, tzinfo=UTC),
            text_body="Price: <script>alert('xss')</script>",
        )
        _render_text_to_pdf(raw)

        call_args = mock_pdf.call_args[0][0]
        assert "<script>" not in call_args
        assert "&lt;script&gt;" in call_args


class TestHtmlToPdfBytes:
    """Integration tests with real weasyprint."""

    @pytest.fixture(autouse=True)
    def _suppress_weasyprint_warnings(self, caplog: pytest.LogCaptureFixture) -> None:
        """Suppress noisy weasyprint CSS warnings in test output."""
        caplog.set_level(logging.ERROR, logger="weasyprint")

    def test_produces_valid_pdf(self) -> None:
        result = _html_to_pdf_bytes("<html><body><p>Hello</p></body></html>")
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_unicode_content(self) -> None:
        result = _html_to_pdf_bytes(
            "<html><body><p>Price: \u20ac42.99</p></body></html>"
        )
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"
