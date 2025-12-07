"""Textual UI screens for Command Center."""

from .dashboard_screen import DashboardScreen
from .aramco_screen import AramcoPipelineScreen
from .commercial_screen import CommercialPipelineScreen
from .owner_kpi_screen import OwnerKPIScreen
from .deal_detail_screen import DealDetailScreen
from .email_drafts_screen import EmailDraftsScreen

__all__ = [
    "DashboardScreen",
    "AramcoPipelineScreen",
    "CommercialPipelineScreen",
    "OwnerKPIScreen",
    "DealDetailScreen",
    "EmailDraftsScreen",
]