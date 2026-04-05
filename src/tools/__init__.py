"""Runtime tools package for the jm-cl-assistant application.

Contains deterministic tool implementations (calculator, unit converter,
web search, etc.) that the Orchestrator dispatches to instead of calling
an LLM for queries where a precise, reliable answer is preferred.
"""

# Import each tool module to trigger its REGISTRY.register() call at
# package load time.  Any new tool added to this package must be imported
# here so the registry is fully populated before first use.
from src.tools import calculator as _calculator  # noqa: F401
from src.tools import converter as _converter  # noqa: F401
from src.tools import currency as _currency  # noqa: F401
from src.tools import datetime_tool as _datetime_tool  # noqa: F401
from src.tools import dictionary as _dictionary  # noqa: F401
from src.tools import location as _location  # noqa: F401
from src.tools import weather as _weather  # noqa: F401
from src.tools import web_search as _web_search  # noqa: F401
