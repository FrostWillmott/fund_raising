import os
from fund_raising.base import *
from fund_raising.development import *

if os.getenv('DJANGO_ENV') == 'production':
    try:
        from fund_raising.production import *
    except ImportError:
        pass
