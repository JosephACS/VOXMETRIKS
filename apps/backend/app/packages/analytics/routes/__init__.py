"""
Analytics routes - API endpoints for statistics and reporting
"""

from .analytics import router as analytics_router
from .smart import router as smart_router
from .stats import router as stats_router

__all__ = ["stats_router", "analytics_router", "smart_router"]
