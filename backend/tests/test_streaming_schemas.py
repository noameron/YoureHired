import pytest
from pydantic import ValidationError

from app.schemas.company_info import (
    CompanySummary,
    StreamCompleteEvent,
    StreamErrorEvent,
    StreamStatusEvent,
    TechStack,
)


# Shared fixtures
@pytest.fixture
def sample_summary() -> CompanySummary:
    """Create a sample CompanySummary for testing."""
    return CompanySummary(
        name="Google",
        industry="Technology",
        description="A leading technology company.",
        size="100,000+ employees",
        tech_stack=TechStack(
            languages=["Python", "Go", "Java"],
            frameworks=["TensorFlow", "Angular"],
            tools=["Kubernetes", "BigQuery"],
        ),
        engineering_culture="Innovation-driven with focus on scale.",
        recent_news=["Launched new AI features"],
        interview_tips="Focus on system design and algorithms.",
        sources=["https://google.com"],
    )


@pytest.fixture
def minimal_summary() -> CompanySummary:
    """Create a minimal CompanySummary with only required fields."""
    return CompanySummary(
        name="Startup",
        description="A new startup company.",
    )


# Parametrized tests for common behavior across all streaming events
class TestStreamingEventCommonBehavior:
    """Tests for behavior common to all streaming event schemas."""

    @pytest.mark.parametrize(
        "event_class,field_name,field_value,expected_type",
        [
            (StreamStatusEvent, "message", "Planning...", "status"),
            (StreamErrorEvent, "message", "Error occurred", "error"),
        ],
    )
    def test_message_events_have_correct_type_and_message(
        self, event_class, field_name, field_value, expected_type
    ):
        """Message-based events are created with correct type and message."""
        # GIVEN a valid message field
        kwargs = {field_name: field_value}

        # WHEN creating the event
        event = event_class(**kwargs)

        # THEN the event has correct type and message
        assert event.type == expected_type
        assert getattr(event, field_name) == field_value

    @pytest.mark.parametrize(
        "event_class,expected_type",
        [
            (StreamStatusEvent, "status"),
            (StreamErrorEvent, "error"),
        ],
    )
    def test_message_events_type_is_immutable(self, event_class, expected_type):
        """Type field is always the literal value regardless of input."""
        # GIVEN an event with message
        event = event_class(message="Test")

        # WHEN accessing type
        # THEN type is the literal value
        assert event.type == expected_type

    @pytest.mark.parametrize(
        "event_class,field_name,field_value,expected_dict",
        [
            (
                StreamStatusEvent,
                "message",
                "Searching...",
                {"type": "status", "message": "Searching..."},
            ),
            (
                StreamErrorEvent,
                "message",
                "Failed",
                {"type": "error", "message": "Failed"},
            ),
        ],
    )
    def test_message_events_serialize_correctly(
        self, event_class, field_name, field_value, expected_dict
    ):
        """Message-based events serialize to dict correctly."""
        # GIVEN an event
        kwargs = {field_name: field_value}
        event = event_class(**kwargs)

        # WHEN serializing to dict
        data = event.model_dump()

        # THEN the dict has correct structure
        assert data == expected_dict

    @pytest.mark.parametrize(
        "event_class",
        [StreamStatusEvent, StreamErrorEvent, StreamCompleteEvent],
    )
    def test_event_rejects_extra_fields_by_default(self, event_class):
        """Events reject extra fields by default (Pydantic default behavior)."""
        # GIVEN extra fields
        if event_class == StreamCompleteEvent:
            kwargs = {
                "data": CompanySummary(name="Test", description="Test company"),
                "extra_field": "should be ignored",
            }
        else:
            kwargs = {"message": "Test", "extra_field": "should be ignored"}

        # WHEN creating event
        event = event_class(**kwargs)

        # THEN extra field is ignored (Pydantic default)
        assert not hasattr(event, "extra_field")


# Edge cases for message-based events
class TestStreamStatusEvent:
    """Tests specific to StreamStatusEvent schema."""

    def test_empty_message_is_valid(self):
        """Empty string message is valid."""
        # GIVEN an empty message

        # WHEN creating a StreamStatusEvent
        event = StreamStatusEvent(message="")

        # THEN the event is valid with empty message
        assert event.type == "status"
        assert event.message == ""

    def test_missing_message_raises_validation_error(self):
        """Missing message field raises validation error."""
        # GIVEN no message field

        # WHEN/THEN creating StreamStatusEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamStatusEvent()

        # THEN error mentions missing field
        assert "message" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_message",
        [123, None, ["list"], {"dict": "value"}],
    )
    def test_invalid_message_type_raises_validation_error(self, invalid_message):
        """Non-string message types raise validation error."""
        # GIVEN an invalid message type

        # WHEN/THEN creating StreamStatusEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamStatusEvent(message=invalid_message)

        # THEN error mentions type issue
        errors = exc_info.value.errors()
        assert any("string" in str(e).lower() for e in errors)


class TestStreamErrorEvent:
    """Tests specific to StreamErrorEvent schema."""

    def test_empty_message_is_valid(self):
        """Empty string message is valid."""
        # GIVEN an empty message

        # WHEN creating a StreamErrorEvent
        event = StreamErrorEvent(message="")

        # THEN the event is valid with empty message
        assert event.type == "error"
        assert event.message == ""

    def test_missing_message_raises_validation_error(self):
        """Missing message field raises validation error."""
        # GIVEN no message field

        # WHEN/THEN creating StreamErrorEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamErrorEvent()

        # THEN error mentions missing field
        assert "message" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_message",
        [123, None, ["list"], {"dict": "value"}],
    )
    def test_invalid_message_type_raises_validation_error(self, invalid_message):
        """Non-string message types raise validation error."""
        # GIVEN an invalid message type

        # WHEN/THEN creating StreamErrorEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamErrorEvent(message=invalid_message)

        # THEN error mentions type issue
        errors = exc_info.value.errors()
        assert any("string" in str(e).lower() for e in errors)


class TestStreamCompleteEvent:
    """Tests specific to StreamCompleteEvent schema."""

    def test_valid_complete_event_with_full_summary(self, sample_summary):
        """Valid complete event is created with full CompanySummary."""
        # GIVEN a fully populated CompanySummary

        # WHEN creating a StreamCompleteEvent
        event = StreamCompleteEvent(data=sample_summary)

        # THEN the event has correct type and data
        assert event.type == "complete"
        assert event.data.name == "Google"
        assert event.data.industry == "Technology"
        assert event.data.tech_stack.languages == ["Python", "Go", "Java"]

    def test_valid_complete_event_with_minimal_summary(self, minimal_summary):
        """Complete event works with minimal CompanySummary."""
        # GIVEN a minimal CompanySummary (only required fields)

        # WHEN creating a StreamCompleteEvent
        event = StreamCompleteEvent(data=minimal_summary)

        # THEN the event is valid with defaults for optional fields
        assert event.type == "complete"
        assert event.data.name == "Startup"
        assert event.data.industry is None
        assert event.data.tech_stack is None

    def test_type_is_always_complete(self, sample_summary):
        """Type field is always 'complete' regardless of input."""
        # GIVEN a complete event

        # WHEN creating without explicit type
        event = StreamCompleteEvent(data=sample_summary)

        # THEN type is the literal value 'complete'
        assert event.type == "complete"

    def test_missing_data_raises_validation_error(self):
        """Missing data field raises validation error."""
        # GIVEN no data field

        # WHEN/THEN creating StreamCompleteEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamCompleteEvent()

        # THEN error mentions missing field
        assert "data" in str(exc_info.value)

    def test_serialization_with_full_summary(self, sample_summary):
        """Event serializes to dict correctly with full summary."""
        # GIVEN a complete event with full summary
        event = StreamCompleteEvent(data=sample_summary)

        # WHEN serializing to dict
        data = event.model_dump()

        # THEN the dict has correct structure
        assert data["type"] == "complete"
        assert data["data"]["name"] == "Google"
        assert data["data"]["industry"] == "Technology"
        assert data["data"]["tech_stack"]["languages"] == ["Python", "Go", "Java"]

    def test_serialization_with_minimal_summary(self, minimal_summary):
        """Event serializes to dict correctly with minimal summary."""
        # GIVEN a complete event with minimal summary
        event = StreamCompleteEvent(data=minimal_summary)

        # WHEN serializing to dict
        data = event.model_dump()

        # THEN the dict has correct structure with None for optional fields
        assert data["type"] == "complete"
        assert data["data"]["name"] == "Startup"
        assert data["data"]["industry"] is None
        assert data["data"]["tech_stack"] is None

    @pytest.mark.parametrize(
        "invalid_data",
        ["string", 123, None, ["list"]],
    )
    def test_invalid_data_type_raises_validation_error(self, invalid_data):
        """Non-CompanySummary data types raise validation error."""
        # GIVEN an invalid data type

        # WHEN/THEN creating StreamCompleteEvent raises ValidationError
        with pytest.raises(ValidationError):
            StreamCompleteEvent(data=invalid_data)

    def test_invalid_company_summary_raises_validation_error(self):
        """Invalid CompanySummary structure raises validation error."""
        # GIVEN a dict missing required CompanySummary fields

        # WHEN/THEN creating StreamCompleteEvent raises ValidationError
        with pytest.raises(ValidationError) as exc_info:
            StreamCompleteEvent(data={"name": "Test"})  # missing description

        # THEN error mentions missing required field
        assert "description" in str(exc_info.value)
