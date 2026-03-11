# Odds Validation Guide

## Overview

The new odds validation system uses **probability-based range validation** instead of exact odds matching. This approach is more flexible and accommodates different Service Providers that may use different odds ladder steps.

## Key Concept

Instead of requiring exact match between calculated odds and SP odds on the ladder, the system validates that:
1. Calculate parlay probability by multiplying individual leg probabilities
2. Convert this combined probability to American odds
3. Find the nearest odds range in the ladder for the SP's odds
4. Check if the calculated odds falls within that range

## Example from Requirements

```python
# Given:
SP odds: +377
Leg 1 probability: 0.8160750396014694
Leg 2 probability: 0.2570033410434336

# Calculation:
Combined probability = 0.8161 × 0.2570 = 0.2097
Calculated odds from 0.2097 = +377 (American odds)

# Find odds range for SP odds +377:
# Ladder contains: [..., 370, 380, 390, ...]
# Range for +377: [370, 380]

# Validation:
Is +377 in range [370, 380]? ✓ YES → VALID
```

## Benefits Over Exact Match

### Old Approach (Exact Match)
- Required calculated odds to exactly match a ladder value
- Would fail if: +377 SP odds vs +375 calculated odds (even if very close)
- Problematic for OddReactor with large ladder gaps (e.g., 50-point steps at high odds)

### New Approach (Range Match)
- Validates if calculated odds falls within adjacent ladder points
- Handles cases like: +377 SP odds vs +375 calculated → both in [370, 380] ✓
- Accommodates different ladder step sizes automatically
- Works for both tight steps (1-point) and wide steps (50-point)

## Ladder Step Analysis

The odds ladder has varying step sizes:

| Odds Range | Step Size | % Difference |
|------------|-----------|--------------|
| 100 → 1000 | 1-20 | ≤ 1% |
| 1000 → 2000 | 50-100 | 2.5-5% |
| 2000+ | 250-500 | 2.5-5% |

By using range validation, all these cases are handled correctly.

## Usage in Code

### Basic Validation

```python
from odds_validation import validate_odds_with_probability

# Validate SP odds against leg probabilities
result = validate_odds_with_probability(
    sp_odds=377,
    leg_probabilities=[0.8161, 0.2570]
)

print(result['valid'])  # True
print(result['explanation'])
# "SP odds: +377, Combined probability: 0.2097, 
#  Calculated odds: +377, Valid range: [+370, +380] -> ✓ VALID"
```

### Validation with price_probability Data

```python
from odds_validation import validate_price_probability

# Validate using price_probability from SP confirmation
price_probability_data = [
    {
        "vig": None,
        "lines": [
            {"line_id": "abc123", "probability": 0.8161},
            {"line_id": "def456", "probability": 0.2570}
        ],
        "max_risk": 5499
    }
]

result = validate_price_probability(
    sp_odds=377,
    price_probability_data=price_probability_data
)

if result['valid']:
    print("✓ Odds validation passed!")
else:
    print(f"✗ Validation failed: {result.get('error', 'Invalid odds')}")
```

## Integration with Confirmation Flow

The validation can be integrated into the SP confirmation process:

```python
def confirm_price(self, price_confirm_request):
    odds = price_confirm_request.get('odds', 100)
    price_probability = price_confirm_request.get('price_probability', [])
    
    # Validate price_probability if provided
    if price_probability:
        validation = validate_price_probability(odds, price_probability)
        
        if not validation['valid']:
            logging.warning(f"⚠️ Odds validation failed: {validation['explanation']}")
            # Decide whether to reject or proceed with warning
    
    # Continue with confirmation...
```

## API Reference

### `american_to_probability(american_odds: int) -> float`
Convert American odds to implied probability.

**Parameters:**
- `american_odds`: American odds format (e.g., +377, -110)

**Returns:**
- Implied probability as decimal (e.g., 0.2096)

### `probability_to_american(probability: float) -> int`
Convert implied probability to American odds.

**Parameters:**
- `probability`: Implied probability as decimal (e.g., 0.21)

**Returns:**
- American odds format (e.g., +377)

### `find_odds_range(american_odds: int) -> tuple[int, int]`
Find the two nearest odds values in the ladder that bracket the given odds.

**Parameters:**
- `american_odds`: The odds to find range for (e.g., +377)

**Returns:**
- Tuple of (lower_odds, upper_odds) that bracket the odds (e.g., (370, 380))

### `validate_odds_with_probability(sp_odds: int, leg_probabilities: List[float]) -> Dict`
Core validation function.

**Parameters:**
- `sp_odds`: The SP's offered odds (e.g., +377)
- `leg_probabilities`: List of probabilities for each leg (e.g., [0.8161, 0.2570])

**Returns:**
Dictionary with:
- `valid`: bool
- `calculated_probability`: float
- `calculated_odds`: int
- `sp_odds`: int
- `odds_range`: tuple[int, int]
- `explanation`: str

### `validate_price_probability(sp_odds: int, price_probability_data: List[Dict]) -> Dict`
High-level validation for price_probability data structure.

**Parameters:**
- `sp_odds`: The SP's offered odds in American format
- `price_probability_data`: List of price_probability entries from SP confirmation

**Returns:**
Validation result dictionary (same structure as `validate_odds_with_probability`)

## Testing

Run the test suite to verify the implementation:

```bash
python test_odds_validation.py
```

Expected output:
```
🎉 ALL TESTS PASSED! 🎉
✓ Odds validation logic is working correctly
✓ Probability-based range validation implemented successfully
```

## Migration Notes

If you're updating from the old exact-match system:

1. Replace exact odds comparisons with calls to `validate_odds_with_probability()`
2. The new system is backward compatible - exact matches still pass validation
3. Range validation provides more flexibility without sacrificing accuracy
4. Consider logging validation results for monitoring and debugging
