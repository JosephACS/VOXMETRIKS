"""
Analytics routes - API endpoints for statistics and reporting
"""

from .stats import router as stats_router
from .analytics import router as analytics_router

__all__ = ["stats_router", "analytics_router"]
