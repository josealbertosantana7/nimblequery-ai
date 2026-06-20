"""Registry of specialist agents, filtered by config feature flags."""
from app.core.config import settings

from . import aero_eng_agent, airport_agent, regs_agent, tracking_agent, weather_agent

_REGISTRY = [
    (regs_agent, settings.enable_regs_agent),
    (weather_agent, settings.enable_weather_agent),
    (tracking_agent, settings.enable_tracking_agent),
    (airport_agent, settings.enable_airport_agent),
    (aero_eng_agent, settings.enable_aero_eng_agent),
]


def enabled_specialists():
    """Return the specialist modules whose feature flag is on."""
    return [mod for mod, enabled in _REGISTRY if enabled]
