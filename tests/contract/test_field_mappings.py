"""Contract tests for frontend/backend field mapping validation.

These tests automatically extract field names from frontend code and validate
that they match the backend API schemas. This approach would have caught:
- Bug #7: `summary` vs `title`, `logged_at` vs `occurred_at`
- Bug #9: Log table showing wrong field
- Bug #10: Log date field not displaying
"""

import ast
from pathlib import Path
from typing import Set

import pytest

from cmd_center.backend.models.employee_models import (
    EmployeeResponse,
    EmployeeWithAggregates,
)
from cmd_center.backend.models.task_models import (
    TaskResponse,
    TaskWithAssignee,
)
from cmd_center.backend.models.note_models import NoteResponse
from cmd_center.backend.models.document_models import DocumentResponse
from cmd_center.backend.models.bonus_models import (
    BonusResponse,
    BonusWithPayments,
)
from cmd_center.backend.models.employee_log_models import (
    LogEntryResponse,
    LogEntryWithEmployee,
)
from cmd_center.backend.models.skill_models import SkillResponse


class FieldExtractor(ast.NodeVisitor):
    """Extract field names from .get() calls in Python code."""

    def __init__(self):
        self.fields: Set[str] = set()

    def visit_Call(self, node):
        """Visit function calls to find .get() patterns."""
        # Match: something.get("field_name", ...)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            self.fields.add(node.args[0].value)
        self.generic_visit(node)


class SubscriptExtractor(ast.NodeVisitor):
    """Extract field names from dict subscript access like item["field"]."""

    def __init__(self):
        self.fields: Set[str] = set()

    def visit_Subscript(self, node):
        """Visit subscript access to find dict["field"] patterns."""
        if isinstance(node.slice, ast.Constant) and isinstance(
            node.slice.value, str
        ):
            self.fields.add(node.slice.value)
        self.generic_visit(node)


def extract_fields_from_file(filepath: Path) -> Set[str]:
    """Extract all field names referenced via .get() or ["field"] in a Python file."""
    source = filepath.read_text()
    tree = ast.parse(source)

    get_extractor = FieldExtractor()
    get_extractor.visit(tree)

    subscript_extractor = SubscriptExtractor()
    subscript_extractor.visit(tree)

    return get_extractor.fields | subscript_extractor.fields


def extract_fields_from_function(filepath: Path, function_name: str) -> Set[str]:
    """Extract fields from a specific function in a file."""
    source = filepath.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            get_extractor = FieldExtractor()
            get_extractor.visit(node)

            subscript_extractor = SubscriptExtractor()
            subscript_extractor.visit(node)

            return get_extractor.fields | subscript_extractor.fields

    return set()


def extract_fields_from_class(filepath: Path, class_name: str) -> Set[str]:
    """Extract fields from a specific class in a file."""
    source = filepath.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            get_extractor = FieldExtractor()
            get_extractor.visit(node)

            subscript_extractor = SubscriptExtractor()
            subscript_extractor.visit(node)

            return get_extractor.fields | subscript_extractor.fields

    return set()


# Common fields that are not entity fields (should be excluded from validation)
COMMON_NON_ENTITY_FIELDS = {
    "items",
    "total",
    "page",
    "page_size",
    "loops",
    "total_runs_today",
    "total_findings_today",
}


class TestTrackerScreenFieldMappings:
    """Test field mappings in tracker_screen.py."""

    SCREENS_DIR = Path("cmd_center/screens")

    def test_render_logs_fields_match_schema(self):
        """Auto-extracted log fields match LogEntryResponse schema."""
        schema_fields = set(LogEntryResponse.model_fields.keys())
        enriched_fields = set(LogEntryWithEmployee.model_fields.keys())
        all_valid = schema_fields | enriched_fields

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "tracker_screen.py", "_render_logs"
        )

        # Filter to entity fields
        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - all_valid
        assert not missing, f"_render_logs references non-existent fields: {missing}"

    def test_render_bonuses_fields_match_schema(self):
        """Auto-extracted bonus fields match BonusResponse schema."""
        schema_fields = set(BonusResponse.model_fields.keys())
        enriched_fields = set(BonusWithPayments.model_fields.keys())
        all_valid = schema_fields | enriched_fields

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "tracker_screen.py", "_render_bonuses"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - all_valid
        assert not missing, f"_render_bonuses references non-existent fields: {missing}"

    def test_render_documents_fields_match_schema(self):
        """Auto-extracted document fields match DocumentResponse schema."""
        schema_fields = set(DocumentResponse.model_fields.keys())

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "tracker_screen.py", "_render_documents"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - schema_fields
        assert not missing, f"_render_documents references non-existent fields: {missing}"

    def test_render_skills_fields_match_schema(self):
        """Auto-extracted skill fields match SkillResponse schema."""
        schema_fields = set(SkillResponse.model_fields.keys())

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "tracker_screen.py", "_render_skills"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - schema_fields
        assert not missing, f"_render_skills references non-existent fields: {missing}"


class TestTeamScreenFieldMappings:
    """Test field mappings in team_screen.py."""

    SCREENS_DIR = Path("cmd_center/screens")

    def test_render_employees_fields_match_schema(self):
        """Auto-extracted employee fields match schema."""
        schema_fields = set(EmployeeResponse.model_fields.keys())
        enriched_fields = set(EmployeeWithAggregates.model_fields.keys())
        all_valid = schema_fields | enriched_fields

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "team_screen.py", "_render_employees"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - all_valid
        assert not missing, f"_render_employees references non-existent fields: {missing}"


class TestManagementScreenFieldMappings:
    """Test field mappings in management_screen.py."""

    SCREENS_DIR = Path("cmd_center/screens")

    def test_render_tasks_fields_match_schema(self):
        """Auto-extracted task fields match TaskResponse schema."""
        schema_fields = set(TaskResponse.model_fields.keys())
        enriched_fields = set(TaskWithAssignee.model_fields.keys())
        all_valid = schema_fields | enriched_fields

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "management_screen.py", "_render_tasks"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - all_valid
        assert not missing, f"_render_tasks references non-existent fields: {missing}"

    def test_render_notes_fields_match_schema(self):
        """Auto-extracted note fields match NoteResponse schema."""
        schema_fields = set(NoteResponse.model_fields.keys())

        frontend_fields = extract_fields_from_function(
            self.SCREENS_DIR / "management_screen.py", "_render_notes"
        )

        entity_fields = {
            f
            for f in frontend_fields
            if not f.startswith("_") and f not in COMMON_NON_ENTITY_FIELDS
        }

        missing = entity_fields - schema_fields
        assert not missing, f"_render_notes references non-existent fields: {missing}"


class TestModalFieldMappings:
    """Test field mappings in modal classes."""

    SCREENS_DIR = Path("cmd_center/screens")

    def test_log_create_modal_fields(self):
        """LogCreateModal uses correct field names."""
        schema_fields = set(LogEntryResponse.model_fields.keys())

        # Extract from LogCreateModal class
        frontend_fields = extract_fields_from_class(
            self.SCREENS_DIR / "tracker_screen.py", "LogCreateModal"
        )

        # Filter to data fields (exclude UI fields)
        data_fields = {
            f
            for f in frontend_fields
            if f
            in {
                "employee_id",
                "category",
                "title",
                "content",
                "severity",
                "occurred_at",
            }
        }

        missing = data_fields - schema_fields
        assert not missing, f"LogCreateModal references non-existent fields: {missing}"

    def test_bonus_create_modal_fields(self):
        """BonusCreateModal uses correct field names."""
        schema_fields = set(BonusResponse.model_fields.keys())

        frontend_fields = extract_fields_from_class(
            self.SCREENS_DIR / "tracker_screen.py", "BonusCreateModal"
        )

        # Filter to data fields
        data_fields = {
            f
            for f in frontend_fields
            if f
            in {
                "employee_id",
                "title",
                "amount",
                "currency",
                "bonus_type",
                "promised_date",
                "due_date",
            }
        }

        missing = data_fields - schema_fields
        assert not missing, f"BonusCreateModal references non-existent fields: {missing}"


class TestComprehensiveFieldCoverage:
    """Comprehensive field coverage across all screens."""

    SCREENS_DIR = Path("cmd_center/screens")

    def test_all_screens_use_valid_fields(self):
        """Check all screen files for field references."""
        # Map of render functions to their schemas
        screen_schema_map = {
            "tracker_screen.py": {
                "_render_documents": [DocumentResponse],
                "_render_bonuses": [BonusResponse, BonusWithPayments],
                "_render_logs": [LogEntryResponse, LogEntryWithEmployee],
                "_render_skills": [SkillResponse],
            },
            "team_screen.py": {
                "_render_employees": [EmployeeResponse, EmployeeWithAggregates],
            },
            "management_screen.py": {
                "_render_tasks": [TaskResponse, TaskWithAssignee],
                "_render_notes": [NoteResponse],
            },
        }

        errors = []
        for filename, functions in screen_schema_map.items():
            filepath = self.SCREENS_DIR / filename
            if not filepath.exists():
                continue

            for func_name, schemas in functions.items():
                frontend_fields = extract_fields_from_function(filepath, func_name)

                # Combine all schema fields
                all_valid = set()
                for schema in schemas:
                    all_valid |= set(schema.model_fields.keys())

                # Filter to entity fields
                entity_fields = {
                    f
                    for f in frontend_fields
                    if f not in COMMON_NON_ENTITY_FIELDS and not f.startswith("_")
                }

                missing = entity_fields - all_valid
                if missing:
                    errors.append(
                        f"{filename}:{func_name} uses unknown fields: {missing}"
                    )

        assert not errors, "\n".join(errors)


class TestFieldExtractionUtility:
    """Test the field extraction utility functions."""

    def test_extract_get_calls(self, tmp_path):
        """Extract field names from .get() calls."""
        code = '''
def render(item):
    name = item.get("name", "")
    age = item.get("age", 0)
    email = item.get("email")
'''
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        fields = extract_fields_from_file(test_file)
        assert fields == {"name", "age", "email"}

    def test_extract_subscript_access(self, tmp_path):
        """Extract field names from subscript access."""
        code = '''
def render(item):
    name = item["name"]
    age = item["age"]
'''
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        fields = extract_fields_from_file(test_file)
        assert fields == {"name", "age"}

    def test_extract_from_specific_function(self, tmp_path):
        """Extract fields from a specific function only."""
        code = '''
def func_a(item):
    return item.get("field_a", "")

def func_b(item):
    return item.get("field_b", "")
'''
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        fields_a = extract_fields_from_function(test_file, "func_a")
        fields_b = extract_fields_from_function(test_file, "func_b")

        assert fields_a == {"field_a"}
        assert fields_b == {"field_b"}

    def test_extract_from_class(self, tmp_path):
        """Extract fields from a specific class."""
        code = '''
class MyModal:
    def compose(self):
        val = self.data.get("field_in_class", "")

def other_func(item):
    return item.get("field_outside", "")
'''
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        class_fields = extract_fields_from_class(test_file, "MyModal")
        assert "field_in_class" in class_fields
        assert "field_outside" not in class_fields
