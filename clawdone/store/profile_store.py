"""Composed ProfileStore implementation."""

from __future__ import annotations

from .core import ProfileStoreCoreMixin
from .metrics import ProfileStoreMetricsMixin
from .sharing import ProfileStoreSharingMixin
from .todos import ProfileStoreTodoMixin

class ProfileStore(ProfileStoreMetricsMixin, ProfileStoreSharingMixin, ProfileStoreTodoMixin, ProfileStoreCoreMixin):
    pass
