"""
Skill decay computation.

The core insight: a skill that hasn't been practiced degrades exponentially.
We use a half-life model: mastery halves every ``half_life_days`` days of inactivity.

Formula: current_mastery = base_mastery × exp(-λ × days_inactive)
Where λ = ln(2) / half_life_days

This mirrors real cognitive science findings on the "forgetting curve"
(Ebbinghaus, 1885) adapted to procedural industrial skills.
"""

import math
from datetime import datetime, timezone


def compute_recency_factor(last_practice: datetime, half_life_days: float = 90.0) -> float:
    """
    Compute the recency/freshness factor for a skill.

    Returns a value between 0 and 1:
    - 1.0  = practiced today (peak condition)
    - 0.5  = not practiced for half_life_days (skill at half strength)
    - ~0.1 = not practiced for ~3× half_life_days (seriously degraded)

    Args:
        last_practice:   UTC datetime of the most recent practice session.
        half_life_days:  Number of days for mastery to halve (default: 90).

    Returns:
        A float in [0, 1] representing skill freshness.
    """
    now = datetime.now(timezone.utc)
    if last_practice.tzinfo is None:
        last_practice = last_practice.replace(tzinfo=timezone.utc)
    days_elapsed = max(0, (now - last_practice).days)
    decay_constant = math.log(2) / half_life_days
    return math.exp(-decay_constant * days_elapsed)


def compute_effective_mastery(
    base_mastery: float,
    last_practice: datetime,
    half_life_days: float = 90.0,
) -> float:
    """
    Compute the effective (decayed) mastery score.

    Args:
        base_mastery:    Raw mastery score 0-100 (from SkillSnapshot).
        last_practice:   UTC datetime of the most recent practice session.
        half_life_days:  Half-life in days (default: 90).

    Returns:
        Effective mastery score, rounded to 2 decimal places.
    """
    recency = compute_recency_factor(last_practice, half_life_days)
    return round(base_mastery * recency, 2)


def days_since(dt: datetime) -> int:
    """
    Return the number of full calendar days elapsed since *dt*.

    Always returns a non-negative integer; never negative even if *dt* is
    slightly in the future due to clock skew.

    Args:
        dt: A datetime object (timezone-aware or naive UTC).

    Returns:
        Number of days elapsed since *dt*.
    """
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (now - dt).days)


def mastery_from_hours(total_hours: float, saturation_hours: float = 200.0) -> float:
    """
    Convert cumulative practice hours into a raw mastery score (0-100).

    Uses a logarithmic learning curve: rapid initial gains that plateau
    as the operator approaches expert-level proficiency.

    Args:
        total_hours:       Total hours ever worked at the operation.
        saturation_hours:  Hours at which mastery is considered ~95% (default: 200h).

    Returns:
        Raw mastery score in [0, 100].
    """
    if total_hours <= 0:
        return 0.0
    # Logistic-inspired growth: 95% mastery at saturation_hours
    k = math.log(19) / saturation_hours  # ln(19) ≈ 2.944 → score=95 at saturation
    score = 100.0 / (1.0 + math.exp(-k * (total_hours - saturation_hours / 2)))
    return round(min(score, 100.0), 2)
