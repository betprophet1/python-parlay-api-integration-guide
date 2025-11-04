"""
Odds Validation Module
Provides probability-based odds validation using odds ladder ranges.

Instead of exact odds matching, this module validates by:
1. Converting American odds to implied probability
2. Calculating parlay probability by multiplying leg probabilities
3. Finding the two nearest odds values in the ladder
4. Checking if calculated odds from probability falls within that range
"""

import constants
from typing import List, Dict, Optional


def american_to_probability(american_odds: int) -> float:
    """
    Convert American odds to implied probability.
    
    Args:
        american_odds: American odds format (e.g., +377, -110)
        
    Returns:
        Implied probability as a decimal (e.g., 0.21)
        
    Examples:
        +377 -> 0.20964 (approximately 0.21)
        -110 -> 0.52381
    """
    if american_odds > 0:
        # For positive odds: probability = 100 / (odds + 100)
        return 100 / (american_odds + 100)
    else:
        # For negative odds: probability = abs(odds) / (abs(odds) + 100)
        return abs(american_odds) / (abs(american_odds) + 100)


def probability_to_american(probability: float) -> int:
    """
    Convert implied probability to American odds.
    
    Args:
        probability: Implied probability as a decimal (e.g., 0.21)
        
    Returns:
        American odds format
        
    Examples:
        0.21 -> +376 (approximately +377)
        0.52381 -> -110
    """
    if probability > 0.5:
        # Favorite: negative odds
        # Formula: -100 * probability / (1 - probability)
        odds = -100 * probability / (1 - probability)
    else:
        # Underdog: positive odds (includes exactly 0.5 as +100)
        # Formula: 100 * (1 - probability) / probability
        odds = 100 * (1 - probability) / probability
    
    return int(round(odds))


def find_odds_range(american_odds: int, odds_ladder: List[int] = None) -> tuple[int, int]:
    """
    Find the two nearest odds values in the ladder that bracket the given odds.
    
    Args:
        american_odds: The odds to find range for (e.g., +377)
        odds_ladder: Optional custom odds ladder, defaults to VALID_ODDS_BACKUP
        
    Returns:
        Tuple of (lower_odds, upper_odds) that bracket the given odds
        
    Examples:
        +377 -> (375, 380) since 375 <= 377 <= 380 in the ladder
        -115 -> (-116, -114) 
    """
    if odds_ladder is None:
        odds_ladder = constants.VALID_ODDS_BACKUP
    
    # If odds exactly matches a ladder value, use it and the next value
    if american_odds in odds_ladder:
        idx = odds_ladder.index(american_odds)
        if idx < len(odds_ladder) - 1:
            return (american_odds, odds_ladder[idx + 1])
        else:
            # Last value in ladder
            return (odds_ladder[idx - 1], american_odds)
    
    # Find the two values that bracket the odds
    for i in range(len(odds_ladder) - 1):
        lower = odds_ladder[i]
        upper = odds_ladder[i + 1]
        
        # Check if odds falls between these two ladder values
        if lower <= american_odds <= upper:
            return (lower, upper)
    
    # If we get here, odds is outside the ladder range
    # Return the closest boundary
    if american_odds < odds_ladder[0]:
        return (odds_ladder[0], odds_ladder[1])
    else:
        return (odds_ladder[-2], odds_ladder[-1])


def validate_odds_with_probability(
    sp_odds: int,
    leg_probabilities: List[float],
    odds_ladder: List[int] = None
) -> Dict[str, any]:
    """
    Validate SP odds against calculated parlay probability using odds range method.
    
    Instead of exact match, this checks if the calculated odds from true probability
    falls within the range of adjacent ladder values around the SP odds.
    
    Args:
        sp_odds: The SP's offered odds (e.g., +377)
        leg_probabilities: List of probabilities for each leg (e.g., [0.8161, 0.2570])
        odds_ladder: Optional custom odds ladder
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "calculated_probability": float,
            "calculated_odds": int,
            "sp_odds": int,
            "odds_range": tuple[int, int],
            "explanation": str
        }
        
    Example:
        SP odds: +377
        Leg probabilities: [0.8161, 0.2570]
        Combined probability: 0.8161 * 0.2570 = 0.2097
        Calculated odds from 0.2097: +375
        Odds range for +377: (375, 380)
        Since 375 is in range [375, 380], validation passes ✓
    """
    if odds_ladder is None:
        odds_ladder = constants.VALID_ODDS_BACKUP
    
    # Calculate combined parlay probability
    combined_probability = 1.0
    for prob in leg_probabilities:
        combined_probability *= prob
    
    # Convert combined probability to American odds
    calculated_odds = probability_to_american(combined_probability)
    
    # Find the odds range for SP odds
    lower_bound, upper_bound = find_odds_range(sp_odds, odds_ladder)
    
    # Validate: calculated odds should fall within the range
    is_valid = lower_bound <= calculated_odds <= upper_bound
    
    result = {
        "valid": is_valid,
        "calculated_probability": combined_probability,
        "calculated_odds": calculated_odds,
        "sp_odds": sp_odds,
        "odds_range": (lower_bound, upper_bound),
        "explanation": (
            f"SP odds: {sp_odds:+d}, "
            f"Combined probability: {combined_probability:.4f}, "
            f"Calculated odds: {calculated_odds:+d}, "
            f"Valid range: [{lower_bound:+d}, {upper_bound:+d}] "
            f"-> {'✓ VALID' if is_valid else '✗ INVALID'}"
        )
    }
    
    return result


def validate_price_probability(
    sp_odds: int,
    price_probability_data: List[Dict]
) -> Dict[str, any]:
    """
    Validate price_probability data against SP odds.
    
    Args:
        sp_odds: The SP's offered odds in American format
        price_probability_data: List of price_probability entries from SP confirmation
            Each entry has structure:
            {
                "lines": [{"line_id": str, "probability": float}, ...],
                "max_risk": int,
                "vig": float
            }
            
    Returns:
        Dictionary with validation results including validity and detailed explanation
    """
    if not price_probability_data or len(price_probability_data) == 0:
        return {
            "valid": False,
            "error": "No price_probability data provided"
        }
    
    # Extract probabilities from the first price_probability entry
    # (typically there's only one entry per confirmation)
    first_entry = price_probability_data[0]
    lines = first_entry.get("lines", [])
    
    if not lines:
        return {
            "valid": False,
            "error": "No lines found in price_probability data"
        }
    
    # Extract leg probabilities
    leg_probabilities = [line.get("probability", 0.5) for line in lines]
    
    # Validate using odds range method
    validation_result = validate_odds_with_probability(sp_odds, leg_probabilities)
    
    return validation_result
