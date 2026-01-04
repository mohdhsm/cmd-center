"""Agent tools for querying data."""

from .registry import ToolRegistry, get_tool_registry
from .base import BaseTool, ToolResult, PendingAction

# Pipeline tools
from .pipeline_tools import GetOverdueDeals, GetStuckDeals, GetDealDetails, GetDealNotes

# Task tools
from .task_tools import GetTasks, GetOverdueTasks, GetPendingReminders, GetNotes

# Employee tools
from .employee_tools import GetEmployees, GetEmployeeDetails, GetEmployeeSkills, GetOwnerKPIs

# Financial tools
from .financial_tools import GetCashflowProjection, GetCEODashboard

# Email tools
from .email_tools import SearchEmails, GetEmails

# Document tools
from .document_tools import GetExpiringDocuments

# HR tools
from .hr_tools import GetUnpaidBonuses

# Knowledge tools
from .knowledge_tools import ReadKnowledge

# Write tools
from .write_tools import (
    RequestCreateTask,
    RequestCreateNote,
    RequestCreateReminder,
    RequestSendEmail,
    RequestUpdateDeal,
    RequestAddDealNote,
)

__all__ = [
    # Registry
    "ToolRegistry",
    "get_tool_registry",
    "BaseTool",
    "ToolResult",
    "PendingAction",
    # Phase 1 tools - Pipeline
    "GetOverdueDeals",
    "GetStuckDeals",
    "GetDealDetails",
    "GetDealNotes",
    # Phase 1 tools - Task
    "GetTasks",
    "GetOverdueTasks",
    "GetPendingReminders",
    "GetNotes",
    # Phase 1 tools - Employee
    "GetEmployees",
    "GetEmployeeDetails",
    "GetEmployeeSkills",
    "GetOwnerKPIs",
    # Phase 2 tools - Financial
    "GetCashflowProjection",
    "GetCEODashboard",
    # Phase 2 tools - Email
    "SearchEmails",
    "GetEmails",
    # Phase 2 tools - Document
    "GetExpiringDocuments",
    # Phase 2 tools - HR
    "GetUnpaidBonuses",
    # Phase 2 tools - Knowledge
    "ReadKnowledge",
    # Phase 3 tools - Write
    "RequestCreateTask",
    "RequestCreateNote",
    "RequestCreateReminder",
    "RequestSendEmail",
    "RequestUpdateDeal",
    "RequestAddDealNote",
]
