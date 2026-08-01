"""
SM-2 spaced repetition algorithm.
"""
from datetime import date, timedelta
from typing import Literal


def update_srs(
    ease: float,
    interval_days: int,
    repetitions: int,
    result: Literal["correct", "incorrect", "unsure"],
    confidence: Literal["guess", "unsure", "certain"]
) -> tuple[float, int, int]:
    """
    Update SRS parameters based on the SM-2 algorithm.

    Args:
        ease: Current ease factor (starts at 2.5)
        interval_days: Current interval in days
        repetitions: Number of consecutive correct repetitions
        result: Whether the answer was correct/incorrect/unsure
        confidence: User's confidence level

    Returns:
        (new_ease, new_interval, new_repetitions)
    """
    # Confidence adjustment: reduce ease if guessing or unsure even when correct
    confidence_penalty = {
        "guess": 0.15,
        "unsure": 0.08,
        "certain": 0.0
    }.get(confidence, 0.0)

    if result == "incorrect":
        # Reset repetitions, reduce ease, schedule for tomorrow
        new_ease = max(1.3, ease - 0.2)
        new_interval = 1
        new_repetitions = 0
    elif result == "unsure":
        # Treat as partially incorrect
        new_ease = max(1.3, ease - 0.15 - confidence_penalty)
        new_interval = max(1, interval_days // 2)  # halve interval
        new_repetitions = max(0, repetitions - 1)
    else:  # correct
        # Standard SM-2
        quality = 4  # Assume "good" response; could be tuned with finer confidence
        new_ease = max(1.3, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)) - confidence_penalty)

        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = int(interval_days * new_ease)

        new_repetitions = repetitions + 1

    return (new_ease, new_interval, new_repetitions)


def calculate_due_date(interval_days: int) -> date:
    """Calculate the next due date."""
    return date.today() + timedelta(days=interval_days)
