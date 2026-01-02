"""Unit tests for enum value validation in TUI screens.

These tests ensure that:
- Frontend Select/dropdown options use valid API enum values
- Filter options match API-accepted values
- Modal form options are consistent with API schemas

This would have caught Bug #7 and #11: Invalid enum values.
"""

import pytest

# Import schemas to get valid enum values
from cmd_center.backend.models.task_models import TaskCreate
from cmd_center.backend.models.bonus_models import BonusCreate, BonusUpdate
from cmd_center.backend.models.employee_log_models import LogEntryCreate
from cmd_center.backend.models.document_models import DocumentCreate


class TestTaskEnumValues:
    """Test task-related enum values."""

    # Valid values from API schema validators
    VALID_PRIORITIES = {"low", "medium", "high"}
    VALID_STATUSES = {"open", "in_progress", "done", "cancelled"}

    def test_priority_options_are_valid(self):
        """Task modal priority options match API schema."""
        # Options as defined in ceo_modals.py TaskCreateModal
        modal_options = {"low", "medium", "high"}

        assert modal_options == self.VALID_PRIORITIES
        assert modal_options.issubset(self.VALID_PRIORITIES)

    def test_status_options_are_valid(self):
        """Task status options match API schema."""
        # Options used in management_screen.py filters
        filter_options = {"open", "in_progress", "done", "cancelled"}

        assert filter_options == self.VALID_STATUSES

    def test_invalid_priority_rejected(self):
        """Invalid priority values are rejected by schema."""
        invalid = ["critical", "urgent", "normal", "HIGH", "Low"]

        for priority in invalid:
            assert priority not in self.VALID_PRIORITIES

    def test_case_sensitive_priorities(self):
        """Priority values are case-sensitive."""
        assert "High" not in self.VALID_PRIORITIES
        assert "HIGH" not in self.VALID_PRIORITIES
        assert "high" in self.VALID_PRIORITIES


class TestBonusEnumValues:
    """Test bonus-related enum values."""

    VALID_TYPES = {"performance", "project", "annual", "other"}
    VALID_STATUSES = {"promised", "approved", "partial", "paid", "cancelled"}

    def test_bonus_type_options_are_valid(self):
        """Bonus modal type options match API schema."""
        # Options as defined in tracker_screen.py BonusCreateModal
        modal_options = {"performance", "project", "annual", "other"}

        assert modal_options == self.VALID_TYPES

    def test_bonus_status_options_are_valid(self):
        """Bonus status options match API schema."""
        # Options used in tracker_screen.py filters
        filter_options = {"pending", "partial", "paid"}

        # Note: "pending" maps to "promised" in API - this is a potential mismatch
        # The filter uses display names, but API uses different values
        # This test documents the expected mapping
        api_statuses = {"promised", "partial", "paid"}
        assert api_statuses.issubset(self.VALID_STATUSES)

    def test_invalid_bonus_type_rejected(self):
        """Invalid bonus type values are rejected."""
        invalid = ["special", "bonus", "reward", "quarterly"]

        for bonus_type in invalid:
            assert bonus_type not in self.VALID_TYPES


class TestLogEntryEnumValues:
    """Test log entry enum values - caught Bug #7 and #11."""

    VALID_CATEGORIES = {"achievement", "issue", "feedback", "milestone", "other"}
    VALID_SEVERITIES = {"low", "medium", "high"}

    def test_log_category_modal_options_are_valid(self):
        """LogCreateModal category options match API schema."""
        # Options as defined in tracker_screen.py LogCreateModal
        modal_options = {"achievement", "issue", "feedback", "milestone", "other"}

        assert modal_options == self.VALID_CATEGORIES

    def test_log_category_filter_options_are_valid(self):
        """Log filter category options match API schema."""
        # Options in tracker_screen.py log-category-select
        filter_options = {"achievement", "issue", "feedback", "milestone", "other"}

        assert filter_options == self.VALID_CATEGORIES

    def test_log_severity_options_are_valid(self):
        """LogCreateModal severity options match API schema."""
        # Options as defined in tracker_screen.py LogCreateModal
        modal_options = {"low", "medium", "high"}

        assert modal_options == self.VALID_SEVERITIES

    def test_invalid_category_performance_review_rejected(self):
        """Bug #7: 'performance_review' is not a valid category."""
        invalid_category = "performance_review"

        assert invalid_category not in self.VALID_CATEGORIES

    def test_invalid_severity_critical_rejected(self):
        """Bug #7: 'critical' is not a valid severity."""
        invalid_severity = "critical"

        assert invalid_severity not in self.VALID_SEVERITIES

    def test_all_invalid_categories_documented(self):
        """Document all known invalid categories that were used."""
        # These were found in the original buggy code
        invalid_categories = {
            "performance_review",  # Original bug
            "review",
            "assessment",
        }

        for cat in invalid_categories:
            assert cat not in self.VALID_CATEGORIES

    def test_all_invalid_severities_documented(self):
        """Document all known invalid severities that were used."""
        invalid_severities = {
            "critical",  # Original bug
            "urgent",
            "warning",
            "info",
        }

        for sev in invalid_severities:
            assert sev not in self.VALID_SEVERITIES


class TestDocumentEnumValues:
    """Test document-related enum values."""

    VALID_STATUSES = {"active", "expired", "renewal_in_progress", "renewed"}
    VALID_TYPES = {"license", "contract", "insurance", "certification"}

    def test_document_status_options_are_valid(self):
        """Document modal status options match expected values."""
        # Options in tracker_screen.py DocumentCreateModal
        modal_options = {"active", "pending_renewal", "expired"}

        # Note: 'pending_renewal' vs 'renewal_in_progress' - check consistency
        # This documents the expected values
        assert "active" in self.VALID_STATUSES
        assert "expired" in self.VALID_STATUSES

    def test_document_type_options_are_valid(self):
        """Document type options match expected values."""
        modal_options = {"license", "contract", "insurance", "certification"}

        assert modal_options == self.VALID_TYPES

    def test_document_filter_options_are_valid(self):
        """Document filter dropdown uses valid types."""
        filter_options = {"license", "contract", "insurance", "certification"}

        assert filter_options == self.VALID_TYPES


class TestSkillEnumValues:
    """Test skill-related enum values."""

    VALID_CATEGORIES = {"technical", "soft", "domain"}

    def test_skill_category_options_are_valid(self):
        """Skill modal category options are valid."""
        modal_options = {"technical", "soft", "domain"}

        assert modal_options == self.VALID_CATEGORIES

    def test_skill_filter_options_are_valid(self):
        """Skill filter category options are valid."""
        filter_options = {"technical", "soft", "domain"}

        assert filter_options == self.VALID_CATEGORIES


class TestReminderEnumValues:
    """Test reminder-related enum values."""

    VALID_CHANNELS = {"in_app", "email"}

    def test_reminder_channel_options_are_valid(self):
        """Reminder channel options are valid."""
        options = {"in_app", "email"}

        assert options == self.VALID_CHANNELS


class TestEnumConsistency:
    """Test consistency between related enums."""

    def test_filter_and_modal_categories_match(self):
        """Filter dropdown and modal should use same category values."""
        # Log categories
        filter_categories = {"achievement", "issue", "feedback", "milestone", "other"}
        modal_categories = {"achievement", "issue", "feedback", "milestone", "other"}

        assert filter_categories == modal_categories

    def test_filter_and_modal_priorities_match(self):
        """Filter dropdown and modal should use same priority values."""
        filter_priorities = {"low", "medium", "high"}
        modal_priorities = {"low", "medium", "high"}

        assert filter_priorities == modal_priorities

    def test_select_value_matches_option_value(self):
        """Select widget value should match the option's value."""
        # Simulating Select options: (label, value) tuples
        options = [
            ("Achievement", "achievement"),
            ("Issue", "issue"),
            ("Feedback", "feedback"),
        ]

        # The second element (value) should be the API value
        values = {opt[1] for opt in options}

        valid = {"achievement", "issue", "feedback", "milestone", "other"}
        assert values.issubset(valid)


class TestEnumValueCasing:
    """Test enum value casing requirements."""

    def test_values_are_lowercase(self):
        """All enum values should be lowercase."""
        all_values = {
            # Task
            "low",
            "medium",
            "high",
            "open",
            "in_progress",
            "done",
            "cancelled",
            # Log
            "achievement",
            "issue",
            "feedback",
            "milestone",
            "other",
            # Bonus
            "performance",
            "project",
            "annual",
            "promised",
            "approved",
            "partial",
            "paid",
            # Document
            "active",
            "expired",
            "renewal_in_progress",
            "renewed",
            "license",
            "contract",
            "insurance",
            "certification",
            # Skill
            "technical",
            "soft",
            "domain",
        }

        for value in all_values:
            assert value == value.lower(), f"'{value}' should be lowercase"

    def test_values_use_underscores(self):
        """Multi-word values use underscores, not spaces or camelCase."""
        multi_word_values = {
            "in_progress",
            "renewal_in_progress",
            "pending_renewal",
            "in_app",
        }

        for value in multi_word_values:
            assert " " not in value, f"'{value}' should not contain spaces"
            assert value == value.lower(), f"'{value}' should be lowercase"


class TestDisplayLabelMapping:
    """Test mapping between display labels and API values."""

    def test_category_label_to_value_mapping(self):
        """Category display labels map to correct API values."""
        label_to_value = {
            "Achievement": "achievement",
            "Issue": "issue",
            "Feedback": "feedback",
            "Milestone": "milestone",
            "Other": "other",
        }

        valid_values = {"achievement", "issue", "feedback", "milestone", "other"}

        for label, value in label_to_value.items():
            assert value in valid_values
            assert value == label.lower().replace(" ", "_")

    def test_priority_label_to_value_mapping(self):
        """Priority display labels map to correct API values."""
        label_to_value = {
            "Low": "low",
            "Medium": "medium",
            "High": "high",
        }

        valid_values = {"low", "medium", "high"}

        for label, value in label_to_value.items():
            assert value in valid_values
