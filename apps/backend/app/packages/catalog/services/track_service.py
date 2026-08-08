""" Backward-compatible facade for track catalog operations."""

from .tracks.detail import (
    get_track_by_id,
    get_track_by_id_raw,
    get_track_detail,
    get_track_features,
)
from .tracks.list import get_tracks, get_tracks_cursor
from .tracks.mutations import create_track, delete_track, update_track
from .tracks.search import search_tracks

__all__ = [
    "create_track",
    "delete_track",
    "get_track_by_id",
    "get_track_by_id_raw",
    "get_track_detail",
    "get_track_features",
    "get_tracks",
    "get_tracks_cursor",
    "search_tracks",
    "update_track",
]
