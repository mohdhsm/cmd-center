"""Fixtures for contract tests."""

from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def sample_employee_response():
    """Sample employee response matching EmployeeResponse schema."""
    return {
        "id": 1,
        "full_name": "Ahmed Al-Farsi",
        "role_title": "Sales Manager",
        "department": "sales",
        "email": "ahmed@company.com",
        "phone": "+966501234567",
        "reports_to_employee_id": None,
        "is_active": True,
        "pipedrive_owner_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }


@pytest.fixture
def sample_task_response():
    """Sample task response matching TaskResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "title": "Complete quarterly report",
        "description": "Finish the Q4 report",
        "assignee_employee_id": 1,
        "created_by": "system",
        "status": "open",
        "priority": "high",
        "is_critical": True,
        "due_at": (now + timedelta(days=2)).isoformat(),
        "completed_at": None,
        "target_type": None,
        "target_id": None,
        "is_archived": False,
        "created_at": now.isoformat(),
        "updated_at": None,
    }


@pytest.fixture
def sample_note_response():
    """Sample note response matching NoteResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "content": "Important meeting notes from client call",
        "created_by": "user",
        "target_type": "deal",
        "target_id": 100,
        "review_at": (now + timedelta(days=7)).isoformat(),
        "pinned": True,
        "tags": "client,important",
        "is_archived": False,
        "created_at": now.isoformat(),
        "updated_at": None,
    }


@pytest.fixture
def sample_document_response():
    """Sample document response matching DocumentResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "title": "Business License",
        "document_type": "license",
        "description": "Main business license",
        "issue_date": (now - timedelta(days=365)).isoformat(),
        "expiry_date": (now + timedelta(days=30)).isoformat(),
        "status": "active",
        "reference_number": "BL-2024-001",
        "issuing_authority": "Ministry of Commerce",
        "responsible_employee_id": 1,
        "created_at": now.isoformat(),
        "updated_at": None,
    }


@pytest.fixture
def sample_bonus_response():
    """Sample bonus response matching BonusResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "employee_id": 1,
        "title": "Q4 Performance Bonus",
        "description": "Bonus for exceeding targets",
        "amount": 5000.0,
        "currency": "SAR",
        "bonus_type": "performance",
        "conditions": "Achieved 120% of target",
        "promised_date": now.isoformat(),
        "due_date": (now + timedelta(days=15)).isoformat(),
        "status": "promised",
        "approved_by": None,
        "approved_at": None,
        "created_at": now.isoformat(),
        "updated_at": None,
    }


@pytest.fixture
def sample_log_entry_response():
    """Sample log entry response matching LogEntryResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "employee_id": 1,
        "category": "achievement",
        "title": "Exceeded sales target",
        "content": "Exceeded sales target by 20% this quarter",
        "severity": "low",
        "is_positive": True,
        "logged_by": "manager",
        "occurred_at": now.isoformat(),
        "created_at": now.isoformat(),
    }


@pytest.fixture
def sample_skill_response():
    """Sample skill response matching SkillResponse schema."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "name": "Python",
        "description": "Python programming language",
        "category": "technical",
        "is_active": True,
        "created_at": now.isoformat(),
    }


# =============================================================================
# CEO Dashboard Fixtures
# =============================================================================


@pytest.fixture
def sample_cash_health_response():
    """Sample cash health response matching CashHealth schema."""
    return {
        "runway_months": 4.2,
        "runway_status": "green",
        "aramco_collected_week": 125000.0,
        "aramco_target_week": 200000.0,
        "commercial_collected_week": 0.0,
        "commercial_target_week": 100000.0,
        "total_collected_week": 125000.0,
        "total_target_week": 300000.0,
        "collection_pct": 41.7,
        "predicted_14d": 340000.0,
        "velocity_pct": 65.0,
        "velocity_status": "yellow",
    }


@pytest.fixture
def sample_urgent_deal_response():
    """Sample urgent deal response matching UrgentDeal schema."""
    return {
        "deal_id": 1001,
        "title": "Aramco Maintenance Contract",
        "reason": "Awaiting GR 23 days",
        "value_sar": 450000.0,
        "stage": "Awaiting GR",
        "owner": "Mohammed",
        "days_stuck": 23,
    }


@pytest.fixture
def sample_pipeline_stage_response():
    """Sample pipeline stage response matching PipelineStage schema."""
    return {
        "name": "Order Received",
        "stage_id": 27,
        "avg_days": 5.2,
        "deal_count": 8,
    }


@pytest.fixture
def sample_pipeline_velocity_response(sample_pipeline_stage_response):
    """Sample pipeline velocity response matching PipelineVelocity schema."""
    return {
        "stages": [
            sample_pipeline_stage_response,
            {"name": "Under Progress", "stage_id": 29, "avg_days": 12.5, "deal_count": 15},
            {"name": "Awaiting MDD", "stage_id": 82, "avg_days": 8.3, "deal_count": 5},
            {"name": "Awaiting GR", "stage_id": 45, "avg_days": 9.0, "deal_count": 3},
        ],
        "current_cycle_days": 35.0,
        "target_cycle_days": 21.0,
        "trend": "worse",
        "trend_pct": 66.7,
    }


@pytest.fixture
def sample_strategic_priority_response():
    """Sample strategic priority response matching StrategicPriority schema."""
    return {
        "name": "Cost Reduction",
        "current": 15.0,
        "target": 20.0,
        "pct": 75.0,
        "status": "yellow",
        "unit": "%",
    }


@pytest.fixture
def sample_sales_scorecard_response():
    """Sample sales scorecard response matching SalesScorecard schema."""
    return {
        "pipeline_value": 2100000.0,
        "won_value": 450000.0,
        "active_deals_count": 28,
        "overdue_count": 3,
        "status": "green",
    }


@pytest.fixture
def sample_ceo_dashboard_response(
    sample_cash_health_response,
    sample_urgent_deal_response,
    sample_pipeline_velocity_response,
    sample_strategic_priority_response,
    sample_sales_scorecard_response,
):
    """Sample complete CEO Dashboard response matching CEODashboardMetrics schema."""
    now = datetime.now(timezone.utc)
    return {
        "cash_health": sample_cash_health_response,
        "urgent_deals": [
            sample_urgent_deal_response,
            {
                "deal_id": 1002,
                "title": "Commercial Installation",
                "reason": "No update 12 days",
                "value_sar": 120000.0,
                "stage": "Under Progress",
                "owner": "Ahmed",
                "days_stuck": 12,
            },
        ],
        "pipeline_velocity": sample_pipeline_velocity_response,
        "strategic_priorities": [
            sample_strategic_priority_response,
            {
                "name": "Sales Pipeline",
                "current": 450.0,
                "target": 500.0,
                "pct": 90.0,
                "status": "green",
                "unit": "K SAR",
            },
            {
                "name": "Commercial Share",
                "current": 32.0,
                "target": 40.0,
                "pct": 80.0,
                "status": "yellow",
                "unit": "%",
            },
        ],
        "department_scorecard": {
            "sales": sample_sales_scorecard_response,
        },
        "last_updated": now.isoformat(),
        "data_freshness": "live",
    }


# =============================================================================
# Deal Health Summary Fixtures
# =============================================================================


@pytest.fixture
def sample_deal_health_context():
    """Sample deal health context matching DealHealthContext schema."""
    now = datetime.now(timezone.utc)
    return {
        "deal_id": 6670,
        "deal_title": "Aramco Office Renovation Phase 2",
        "stage": "Awaiting Payment",
        "stage_code": "AP",
        "days_in_stage": 12,
        "owner_name": "Mohammed",
        "value_sar": 450000.0,
        "notes": [
            {
                "date": (now - timedelta(days=3)).isoformat(),
                "author": "Ahmed",
                "content": "Called client, waiting for payment confirmation"
            },
            {
                "date": (now - timedelta(days=7)).isoformat(),
                "author": "Mohammed",
                "content": "Invoice sent to client"
            },
        ],
        "stage_history": [
            {
                "stage_name": "Order Received",
                "entered_at": (now - timedelta(days=30)).isoformat(),
                "duration_hours": 168.0
            },
            {
                "stage_name": "Approved",
                "entered_at": (now - timedelta(days=23)).isoformat(),
                "duration_hours": 120.0
            },
            {
                "stage_name": "Awaiting Payment",
                "entered_at": (now - timedelta(days=12)).isoformat(),
                "duration_hours": 288.0
            },
        ],
        "last_activity_date": (now - timedelta(days=3)).isoformat(),
        "days_since_last_note": 3,
    }


@pytest.fixture
def sample_deal_health_result():
    """Sample deal health result matching DealHealthResult schema."""
    return {
        "deal_id": 6670,
        "health_status": "at_risk",
        "status_flag": "PAYMENT_ISSUE",
        "summary": "Deal has been in Awaiting Payment stage for 12 days, approaching the 14-day critical threshold. Last communication was 3 days ago.",
        "days_in_stage": 12,
        "stage_threshold_warning": 7,
        "stage_threshold_critical": 14,
        "communication_gap_days": 3,
        "communication_assessment": "Healthy",
        "blockers": ["Payment confirmation pending from client"],
        "attribution": "customer_delay",
        "recommended_action": "Follow up with client finance department on payment status. Consider escalating if no response within 48 hours.",
        "confidence": 0.85,
    }


@pytest.fixture
def sample_deal_health_result_healthy():
    """Sample healthy deal result."""
    return {
        "deal_id": 1234,
        "health_status": "healthy",
        "status_flag": None,
        "summary": "Deal is progressing well with regular communication and no blockers identified.",
        "days_in_stage": 5,
        "stage_threshold_warning": 7,
        "stage_threshold_critical": 14,
        "communication_gap_days": 2,
        "communication_assessment": "Healthy",
        "blockers": [],
        "attribution": "none",
        "recommended_action": "Continue regular follow-ups and monitor progress.",
        "confidence": 0.92,
    }


@pytest.fixture
def sample_deal_health_result_critical():
    """Sample critical deal result."""
    return {
        "deal_id": 5555,
        "health_status": "critical",
        "status_flag": "SITE_BLOCKED",
        "summary": "Deal has been stuck in Awaiting Site Readiness for 35 days. Site preparation has been delayed multiple times.",
        "days_in_stage": 35,
        "stage_threshold_warning": 14,
        "stage_threshold_critical": 30,
        "communication_gap_days": 18,
        "communication_assessment": "Communication Gap",
        "blockers": ["Site not ready", "Contractor scheduling conflict", "Missing permits"],
        "attribution": "site_blocked",
        "recommended_action": "Escalate to project management immediately. Schedule urgent site visit to assess blockers.",
        "confidence": 0.78,
    }
