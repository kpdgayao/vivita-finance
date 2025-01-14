# This file makes the views directory a Python package

from . import dashboard
from . import settings
from . import suppliers
from . import expenses
from . import purchase_requests

__all__ = ['dashboard', 'settings', 'suppliers', 'expenses', 'purchase_requests']
