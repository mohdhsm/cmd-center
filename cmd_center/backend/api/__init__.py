"""FastAPI route handlers."""

from fastapi import APIRouter
from . import health, dashboard, aramco, commercial, owners, deals, emails, sync
from . import employees, interventions, reminders, tasks, notes
from . import documents, bonuses, employee_logs, skills
from . import loops
from . import ceo_dashboard

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(aramco.router, prefix="/aramco", tags=["aramco"])
api_router.include_router(commercial.router, prefix="/commercial", tags=["commercial"])
api_router.include_router(owners.router, prefix="/owners", tags=["owners"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])

# CEO Dashboard routers
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(interventions.router, prefix="/interventions", tags=["interventions"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])

# Tracker Module routers
api_router.include_router(documents.router)
api_router.include_router(bonuses.router)
api_router.include_router(employee_logs.router)
api_router.include_router(skills.router)

# Loop Engine routers
api_router.include_router(loops.router)

# CEO Dashboard router
api_router.include_router(ceo_dashboard.router)

__all__ = ["api_router"]