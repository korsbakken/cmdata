"""Provides functionality for caching metadata and data read from files."""

from __future__ import annotations
import typing as tp

import pydantic


class CachedData(pydantic.BaseModel):
    """Empty base class for classes storing cached data"""
    pass
###END class Cached Data

