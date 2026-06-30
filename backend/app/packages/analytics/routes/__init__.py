"""
Analytics routes - API endpoints for statistics and reporting
"""

from .analytics import router as analytics_router
from .stats import router as stats_router

__all__ = ["stats_router", "analytics_router"]
