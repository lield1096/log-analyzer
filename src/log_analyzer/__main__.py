"""Allow ``python -m log_analyzer``."""

import sys

from .cli import main

sys.exit(main())
