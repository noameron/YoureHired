from app.utils.sanitization import sanitize_input


class TestWhitespaceNormalization:
    """Tests for whitespace normalization behavior."""

    def test_strips_leading_trailing_whitespace(self):
        # GIVEN text with leading and trailing whitespace
        text = "  hello world  "

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN whitespace is stripped
        assert result == "hello world"

    def test_normalizes_multiple_spaces(self):
        # GIVEN text with multiple consecutive spaces
        text = "hello    world"

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN multiple spaces become single space
        assert result == "hello world"

    def test_normalizes_tabs_and_newlines(self):
        # GIVEN text with tabs and newlines
        text = "hello\t\nworld"

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN tabs and newlines become single space
        assert result == "hello world"

    def test_handles_only_whitespace(self):
        # GIVEN text containing only whitespace characters
        text = "   \t\n   "

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN result is empty string
        assert result == ""


class TestLengthEnforcement:
    """Tests for max length enforcement."""

    def test_enforces_custom_max_length(self):
        # GIVEN text longer than the max length
        long_text = "a" * 100

        # WHEN sanitizing with a custom max length
        result = sanitize_input(long_text, max_length=50)

        # THEN result is truncated to max length
        assert len(result) == 50

    def test_uses_default_max_length(self):
        # GIVEN text longer than the default max length (8000)
        long_text = "a" * 10000

        # WHEN sanitizing without specifying max length
        result = sanitize_input(long_text)

        # THEN result is truncated to 8000 characters
        assert len(result) == 8000


class TestEdgeCases:
    """Tests for edge cases."""

    def test_handles_empty_string(self):
        # GIVEN an empty string
        text = ""

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN result is empty string
        assert result == ""

    def test_preserves_normal_text(self):
        # GIVEN normal text without extra whitespace
        text = "This is a normal sentence."

        # WHEN sanitizing the input
        result = sanitize_input(text)

        # THEN text is unchanged
        assert result == text
