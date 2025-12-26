"""Unit tests for SkillService."""

from datetime import datetime, timezone

import pytest

from cmd_center.backend.services.skill_service import SkillService
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.models.skill_models import (
    SkillCreate,
    SkillUpdate,
    SkillFilters,
    SkillRatingCreate,
    SkillRatingFilters,
)
from cmd_center.backend.models.employee_models import EmployeeCreate


class TestSkillService:
    """Test cases for SkillService."""

    # =========================================================================
    # Skill CRUD Tests
    # =========================================================================

    def test_create_skill(self, override_db):
        """Creates skill definition."""
        service = SkillService(actor="admin")
        data = SkillCreate(
            name="Python Programming",
            description="Ability to write Python code",
            category="Technical",
        )
        result = service.create_skill(data)

        assert result.id is not None
        assert result.name == "Python Programming"
        assert result.category == "Technical"
        assert result.is_active is True

    def test_get_skill_by_id(self, override_db):
        """Can retrieve skill by ID."""
        service = SkillService()
        created = service.create_skill(SkillCreate(
            name="Test Skill",
            category="General",
        ))

        result = service.get_skill_by_id(created.id)
        assert result is not None
        assert result.id == created.id

    def test_get_skill_by_name(self, override_db):
        """Can retrieve skill by name."""
        service = SkillService()
        service.create_skill(SkillCreate(
            name="Unique Skill Name",
            category="General",
        ))

        result = service.get_skill_by_name("Unique Skill Name")
        assert result is not None
        assert result.name == "Unique Skill Name"

    def test_get_skills_filter_by_category(self, override_db):
        """Filter skills by category."""
        service = SkillService()
        service.create_skill(SkillCreate(name="Python", category="Technical"))
        service.create_skill(SkillCreate(name="Leadership", category="Soft Skills"))
        service.create_skill(SkillCreate(name="JavaScript", category="Technical"))

        result = service.get_skills(SkillFilters(category="Technical"))
        assert result.total == 2
        assert all(s.category == "Technical" for s in result.items)

    def test_get_skills_filter_by_active(self, override_db):
        """Filter skills by is_active."""
        service = SkillService()
        active = service.create_skill(SkillCreate(name="Active Skill", category="General"))
        inactive = service.create_skill(SkillCreate(name="Inactive Skill", category="General"))
        service.deactivate_skill(inactive.id)

        result = service.get_skills(SkillFilters(is_active=True))
        assert result.total == 1
        assert result.items[0].name == "Active Skill"

    def test_get_skills_search(self, override_db):
        """Search skills by name."""
        service = SkillService()
        service.create_skill(SkillCreate(name="Python Programming", category="Technical"))
        service.create_skill(SkillCreate(name="Java Development", category="Technical"))

        result = service.get_skills(SkillFilters(search="python"))
        assert result.total == 1
        assert result.items[0].name == "Python Programming"

    def test_update_skill(self, override_db):
        """Update skill fields."""
        service = SkillService()
        created = service.create_skill(SkillCreate(
            name="Original Name",
            category="Original Category",
        ))

        result = service.update_skill(created.id, SkillUpdate(
            name="Updated Name",
            category="Updated Category",
        ))

        assert result is not None
        assert result.name == "Updated Name"
        assert result.category == "Updated Category"

    def test_deactivate_skill(self, override_db):
        """Deactivate sets is_active to False."""
        service = SkillService()
        created = service.create_skill(SkillCreate(
            name="To Deactivate",
            category="General",
        ))

        result = service.deactivate_skill(created.id)
        assert result.is_active is False

    # =========================================================================
    # Skill Rating Tests
    # =========================================================================

    def test_rate_employee_skill(self, override_db):
        """Creates skill rating."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = SkillService(actor="manager")
        skill = service.create_skill(SkillCreate(name="Python", category="Technical"))

        data = SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=4,
            notes="Good proficiency in Python.",
        )
        result = service.rate_employee_skill(data)

        assert result.id is not None
        assert result.rating == 4
        assert result.rated_by == "manager"

    def test_get_latest_skill_ratings(self, override_db):
        """Returns latest rating per skill per employee."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = SkillService()
        skill = service.create_skill(SkillCreate(name="Python", category="Technical"))

        # Rate twice - should only return the latest
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=3,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=5,
        ))

        result = service.get_latest_skill_ratings(employee.id)
        assert len(result) == 1
        assert result[0].rating == 5

    def test_get_employee_skill_card(self, override_db):
        """Returns all skills with ratings for employee."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="John Developer",
            role_title="Developer",
        ))

        service = SkillService()
        python = service.create_skill(SkillCreate(name="Python", category="Technical"))
        java = service.create_skill(SkillCreate(name="Java", category="Technical"))
        leadership = service.create_skill(SkillCreate(name="Leadership", category="Soft Skills"))

        # Only rate Python
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=python.id,
            rating=5,
        ))

        result = service.get_employee_skill_card(employee.id)
        assert result is not None
        assert result.employee_name == "John Developer"
        assert len(result.skills) == 3

        # Find Python skill
        python_skill = next(s for s in result.skills if s.skill_name == "Python")
        assert python_skill.rating == 5

        # Java should have no rating
        java_skill = next(s for s in result.skills if s.skill_name == "Java")
        assert java_skill.rating is None

    def test_get_skill_rating_history(self, override_db):
        """Get rating history for an employee's skill."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = SkillService()
        skill = service.create_skill(SkillCreate(name="Python", category="Technical"))

        # Rate multiple times
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=2,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=3,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=4,
        ))

        result = service.get_skill_rating_history(employee.id, skill.id)
        assert len(result) == 3
        # Should be ordered by rated_at desc
        assert result[0].rating == 4  # Latest first

    def test_get_top_rated_employees(self, override_db):
        """Get top-rated employees for a skill."""
        emp_service = EmployeeService()
        emp1 = emp_service.create_employee(EmployeeCreate(full_name="High Performer", role_title="Dev"))
        emp2 = emp_service.create_employee(EmployeeCreate(full_name="Medium Performer", role_title="Dev"))
        emp3 = emp_service.create_employee(EmployeeCreate(full_name="Low Performer", role_title="Dev"))

        service = SkillService()
        skill = service.create_skill(SkillCreate(name="Python", category="Technical"))

        service.rate_employee_skill(SkillRatingCreate(
            employee_id=emp1.id,
            skill_id=skill.id,
            rating=5,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=emp2.id,
            skill_id=skill.id,
            rating=3,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=emp3.id,
            skill_id=skill.id,
            rating=2,
        ))

        result = service.get_top_rated_employees(skill.id, limit=2)
        assert len(result) == 2
        assert result[0].rating == 5
        assert result[0].employee_name == "High Performer"
        assert result[1].rating == 3

    def test_get_skill_ratings_filter_min_rating(self, override_db):
        """Filter ratings by minimum rating."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = SkillService()
        skill1 = service.create_skill(SkillCreate(name="Skill 1", category="Technical"))
        skill2 = service.create_skill(SkillCreate(name="Skill 2", category="Technical"))

        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill1.id,
            rating=2,
        ))
        service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill2.id,
            rating=4,
        ))

        result = service.get_skill_ratings(SkillRatingFilters(min_rating=3))
        assert len(result) == 1
        assert result[0].rating == 4

    def test_get_skill_rating_by_id(self, override_db):
        """Get skill rating with skill and employee names."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Jane Developer",
            role_title="Developer",
        ))

        service = SkillService()
        skill = service.create_skill(SkillCreate(name="Python", category="Technical"))

        rating = service.rate_employee_skill(SkillRatingCreate(
            employee_id=employee.id,
            skill_id=skill.id,
            rating=5,
        ))

        result = service.get_skill_rating_by_id(rating.id)
        assert result is not None
        assert result.skill_name == "Python"
        assert result.employee_name == "Jane Developer"
        assert result.rating == 5

    def test_skill_rating_not_found(self, override_db):
        """Returns None for non-existent skill rating."""
        service = SkillService()
        result = service.get_skill_rating_by_id(99999)
        assert result is None

    def test_employee_skill_card_not_found(self, override_db):
        """Returns None for non-existent employee."""
        service = SkillService()
        result = service.get_employee_skill_card(99999)
        assert result is None

    def test_skills_sorted_by_category_and_name(self, override_db):
        """Skills are sorted by category then name."""
        service = SkillService()
        service.create_skill(SkillCreate(name="Zebra", category="B Category"))
        service.create_skill(SkillCreate(name="Apple", category="A Category"))
        service.create_skill(SkillCreate(name="Banana", category="A Category"))

        result = service.get_skills()
        assert result.items[0].category == "A Category"
        assert result.items[0].name == "Apple"
        assert result.items[1].category == "A Category"
        assert result.items[1].name == "Banana"
        assert result.items[2].category == "B Category"
