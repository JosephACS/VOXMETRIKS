"""
Analytics routes - API endpoints for statistics and reporting
"""

from .stats import router as stats_router

__all__ = ["stats_router"]
