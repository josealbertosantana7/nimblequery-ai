"""Pure, deterministic aviation performance calculators.

These functions contain NO LangChain / network imports so they stay trivially
unit-testable. `get_calculator_tools()` lazily wraps them as LangChain tools for
the aerospace-engineering agent.

All results are estimates for training/study only — never for operational use.
"""
import math
from typing import List

ISA_SEA_LEVEL_TEMP_C = 15.0
ISA_LAPSE_C_PER_1000FT = 1.98


def pressure_altitude(field_elevation_ft: float, altimeter_inhg: float) -> float:
    """Pressure altitude (ft) from field elevation and altimeter setting."""
    return field_elevation_ft + (29.92 - altimeter_inhg) * 1000.0


def density_altitude(pressure_altitude_ft: float, oat_celsius: float) -> float:
    """Density altitude (ft), using the standard ~118.8 ft/°C deviation rule."""
    isa_temp = ISA_SEA_LEVEL_TEMP_C - ISA_LAPSE_C_PER_1000FT * (pressure_altitude_ft / 1000.0)
    return pressure_altitude_ft + 118.8 * (oat_celsius - isa_temp)


def wind_components(wind_dir_deg: float, wind_speed_kt: float, runway_heading_deg: float) -> dict:
    """Headwind/crosswind components (kt). Positive headwind = into the nose;
    negative headwind = tailwind. Crosswind is the absolute magnitude."""
    angle = math.radians((wind_dir_deg - runway_heading_deg + 180) % 360 - 180)
    return {
        "headwind_kt": round(wind_speed_kt * math.cos(angle), 1),
        "crosswind_kt": round(abs(wind_speed_kt * math.sin(angle)), 1),
        "from_left": math.sin(angle) < 0,
    }


def weight_and_balance(weights_lb: List[float], arms_in: List[float]) -> dict:
    """Total weight (lb), total moment (lb-in) and CG (in aft of datum)."""
    if len(weights_lb) != len(arms_in):
        raise ValueError("weights_lb and arms_in must have the same length")
    if not weights_lb:
        raise ValueError("at least one station is required")
    total_w = sum(weights_lb)
    total_m = sum(w * a for w, a in zip(weights_lb, arms_in))
    if total_w == 0:
        raise ValueError("total weight is zero")
    return {
        "total_weight_lb": round(total_w, 1),
        "total_moment_lb_in": round(total_m, 1),
        "cg_in": round(total_m / total_w, 2),
    }


def adjust_ground_roll(sea_level_roll_ft: float, density_altitude_ft: float) -> float:
    """Rough density-altitude correction for ground roll (~10% per 1000 ft DA).
    A rule-of-thumb estimate ONLY — always use the aircraft POH for real numbers."""
    return round(sea_level_roll_ft * (1.10 ** (density_altitude_ft / 1000.0)), 0)


def get_calculator_tools():
    """Lazily build LangChain tools (imported here so this module stays pure)."""
    from langchain_core.tools import tool

    @tool
    def pressure_altitude_tool(field_elevation_ft: float, altimeter_inhg: float) -> str:
        """Compute pressure altitude (ft) from field elevation (ft) and altimeter setting (inHg)."""
        return f"Pressure altitude ≈ {pressure_altitude(field_elevation_ft, altimeter_inhg):.0f} ft"

    @tool
    def density_altitude_tool(pressure_altitude_ft: float, oat_celsius: float) -> str:
        """Compute density altitude (ft) from pressure altitude (ft) and outside air temp (°C)."""
        return f"Density altitude ≈ {density_altitude(pressure_altitude_ft, oat_celsius):.0f} ft"

    @tool
    def wind_components_tool(wind_dir_deg: float, wind_speed_kt: float, runway_heading_deg: float) -> str:
        """Headwind and crosswind components (kt) for a runway given the wind."""
        c = wind_components(wind_dir_deg, wind_speed_kt, runway_heading_deg)
        side = "left" if c["from_left"] else "right"
        return (f"Headwind {c['headwind_kt']} kt, crosswind {c['crosswind_kt']} kt "
                f"from the {side}.")

    @tool
    def weight_and_balance_tool(weights_lb: List[float], arms_in: List[float]) -> str:
        """Total weight, moment and CG from parallel lists of station weights (lb) and arms (in)."""
        r = weight_and_balance(weights_lb, arms_in)
        return (f"Total {r['total_weight_lb']} lb, moment {r['total_moment_lb_in']} lb-in, "
                f"CG {r['cg_in']} in aft of datum. Verify against the POH envelope.")

    return [
        pressure_altitude_tool,
        density_altitude_tool,
        wind_components_tool,
        weight_and_balance_tool,
    ]
