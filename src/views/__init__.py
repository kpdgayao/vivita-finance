# This file makes the views directory a Python package

from . import dashboard
from . import settings
from . import suppliers
from . import expenses

__all__ = ['dashboard', 'settings', 'suppliers', 'expenses']
