"""Business logic services for Command Center."""

from .deal_health_service import DealHealthService, get_deal_health_service
from .llm_analysis_service import LLMAnalysisService, get_llm_analysis_service
from .cashflow_service import CashflowService, get_cashflow_service
from .owner_kpi_service import OwnerKPIService, get_owner_kpi_service
from .email_service import EmailService, get_email_service
from .dashboard_service import DashboardService, get_dashboard_service
from .aramco_summary_service import AramcoSummaryService, get_aramco_summary_service

# CEO Dashboard services
from .employee_service import EmployeeService, get_employee_service
from .intervention_service import (
    InterventionService,
    get_intervention_service,
    log_action,
)
from .reminder_service import ReminderService, get_reminder_service
from .task_service import TaskService, get_task_service
from .note_service import NoteService, get_note_service

# Tracker Module services
from .document_service import DocumentService, get_document_service
from .bonus_service import BonusService, get_bonus_service
from .employee_log_service import EmployeeLogService, get_employee_log_service
from .skill_service import SkillService, get_skill_service

# Loop Engine services
from .loop_engine import (
    BaseLoop,
    LoopRegistry,
    LoopService,
    loop_registry,
    get_loop_service,
)
from .loops import (
    DocsExpiryLoop,
    BonusDueLoop,
    TaskOverdueLoop,
    ReminderProcessingLoop,
)

__all__ = [
    # Existing services
    "DealHealthService",
    "get_deal_health_service",
    "LLMAnalysisService",
    "get_llm_analysis_service",
    "CashflowService",
    "get_cashflow_service",
    "OwnerKPIService",
    "get_owner_kpi_service",
    "EmailService",
    "get_email_service",
    "DashboardService",
    "get_dashboard_service",
    "AramcoSummaryService",
    "get_aramco_summary_service",
    # CEO Dashboard services
    "EmployeeService",
    "get_employee_service",
    "InterventionService",
    "get_intervention_service",
    "log_action",
    "ReminderService",
    "get_reminder_service",
    "TaskService",
    "get_task_service",
    "NoteService",
    "get_note_service",
    # Tracker Module services
    "DocumentService",
    "get_document_service",
    "BonusService",
    "get_bonus_service",
    "EmployeeLogService",
    "get_employee_log_service",
    "SkillService",
    "get_skill_service",
    # Loop Engine services
    "BaseLoop",
    "LoopRegistry",
    "LoopService",
    "loop_registry",
    "get_loop_service",
    "DocsExpiryLoop",
    "BonusDueLoop",
    "TaskOverdueLoop",
    "ReminderProcessingLoop",
]