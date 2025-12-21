from unittest.mock import patch

import pytest

from apps.case.documents.tasks import (
    extract_existing_text,
    has_sufficient_text,
    process_document_ocr,
    retry_failed_ocr,
    sanitize_text,
)

pytestmark = pytest.mark.django_db


class TestSanitizeText:
    def test_removes_nul_characters(self):
        """NUL bytes should be stripped."""
        text = "Hello\x00World"
        assert sanitize_text(text) == "HelloWorld"

    def test_preserves_newlines_and_tabs(self):
        """Newlines and tabs should be preserved."""
        text = "Line1\nLine2\tTabbed"
        assert sanitize_text(text) == "Line1\nLine2\tTabbed"

    def test_removes_control_characters(self):
        """Control characters (except newline/tab/cr) should be stripped."""
        text = "Hello\x01\x02\x03World"
        assert sanitize_text(text) == "HelloWorld"

    def test_handles_none(self):
        """None input should return None."""
        assert sanitize_text(None) is None

    def test_handles_empty_string(self):
        """Empty string should return empty string."""
        assert sanitize_text("") == ""


class TestExtractExistingText:
    def test_extracts_text_from_pdf(self, pdf_file):
        """Test text extraction from a PDF."""
        text, page_count, content_chars = extract_existing_text(pdf_file.read())
        assert page_count >= 1
        assert "--- Page 1 ---" in text
        assert isinstance(content_chars, int)

    def test_returns_page_count(self, pdf_file):
        """Test that page count is returned correctly."""
        _, page_count, _ = extract_existing_text(pdf_file.read())
        assert page_count == 1

    def test_content_chars_excludes_headers(self, pdf_file):
        """Test that content_chars doesn't count page header text."""
        text, page_count, content_chars = extract_existing_text(pdf_file.read())
        # The page header "--- Page 1 ---" should not be counted in content_chars
        assert content_chars < len(text)


class TestHasSufficientText:
    def test_sufficient_text(self):
        content_chars = 600
        assert has_sufficient_text(content_chars) is True

    def test_insufficient_text(self):
        content_chars = 400
        assert has_sufficient_text(content_chars) is False

    def test_zero_chars(self):
        assert has_sufficient_text(0) is False

    def test_custom_threshold(self):
        assert has_sufficient_text(50, threshold=30) is True
        assert has_sufficient_text(50, threshold=100) is False


class TestProcessDocumentOcr:
    @patch("apps.case.documents.tasks.default_storage")
    def test_skips_non_pdf(self, mock_storage, document):
        """Non-PDF files should be marked as not_applicable."""
        document.file.name = "documents/1/test.docx"
        document.save()

        process_document_ocr(document.id)

        document.refresh_from_db()
        assert document.ocr_status == "not_applicable"

    def test_nonexistent_document(self):
        """Processing a non-existent document should not raise."""
        process_document_ocr(99999)  # Should not raise

    @patch("apps.case.documents.tasks.default_storage")
    @patch("apps.case.documents.tasks.extract_existing_text")
    def test_extracts_existing_text_layer(self, mock_extract, mock_storage, document):
        """PDF with existing text layer should use extraction, not OCR."""
        mock_storage.open.return_value.__enter__.return_value.read.return_value = (
            b"PDF content"
        )
        # Return text with > 500 content chars so OCR is skipped
        mock_extract.return_value = ("a" * 600, 5, 600)

        process_document_ocr(document.id)

        document.refresh_from_db()
        assert document.ocr_status == "extracted"
        assert document.ocr_text == "a" * 600
        assert document.page_count == 5

    @patch("apps.case.documents.tasks.default_storage")
    @patch("apps.case.documents.tasks.extract_existing_text")
    @patch("apps.case.documents.tasks.run_ocrmypdf")
    def test_runs_ocr_when_needed(self, mock_ocr, mock_extract, mock_storage, document):
        """PDF without sufficient text should run OCR."""
        mock_storage.open.return_value.__enter__.return_value.read.return_value = (
            b"PDF content"
        )
        # First call returns insufficient content chars, second call (after OCR) returns more
        mock_extract.side_effect = [
            ("short", 3, 5),  # Before OCR - only 5 content chars
            ("a" * 600, 3, 600),  # After OCR
        ]
        mock_ocr.return_value = b"OCR'd PDF content"

        process_document_ocr(document.id)

        document.refresh_from_db()
        assert document.ocr_status == "completed"
        assert mock_ocr.called

    @patch("apps.case.documents.tasks.default_storage")
    @patch("apps.case.documents.tasks.extract_existing_text")
    def test_handles_error(self, mock_extract, mock_storage, document):
        """Errors during OCR should be captured."""
        mock_storage.open.return_value.__enter__.return_value.read.side_effect = (
            Exception("Storage error")
        )

        process_document_ocr(document.id)

        document.refresh_from_db()
        assert document.ocr_status == "failed"
        assert "Storage error" in document.ocr_error


class TestRetryFailedOcr:
    @patch("apps.case.documents.tasks.process_document_ocr")
    def test_resets_status_and_retries(self, mock_process, document):
        """Retry should reset status and call process_document_ocr."""
        document.ocr_status = "failed"
        document.ocr_error = "Previous error"
        document.save()

        retry_failed_ocr(document.id)

        document.refresh_from_db()
        mock_process.assert_called_once_with(document.id)
