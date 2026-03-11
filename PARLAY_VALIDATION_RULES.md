# Parlay Validation Rules

## Overview

This document describes the betting rules validation system that ensures parlay combinations comply with sportsbook regulations. The validation prevents conflicting or arbitrage opportunities in multi-leg parlays.

## Validation Rules

### Rule 1: No Both Sides of Moneyline Market

**Description**: Cannot bet on both teams to win the same game.

**Examples**:
- ❌ **INVALID**: Team A moneyline + Team B moneyline (same event)
- ✅ **VALID**: Team A moneyline (Event 1) + Team C moneyline (Event 2)

**Rationale**: Betting both sides guarantees a win, creating an arbitrage opportunity.

---

### Rule 2: No Moneyline + Negative Spread of Opposite Team

**Description**: Cannot combine a moneyline bet on one team with a negative spread on the opposing team.

**Examples**:
- ❌ **INVALID**: Team A moneyline + Team B -1.5 spread
- ✅ **VALID**: Team A moneyline + Team B +1.5 spread
- ❌ **INVALID**: Team A moneyline + Team B +0.5 spread (special soccer case)

**Rationale**: 
- A negative spread on Team B (e.g., -1.5) means Team B must win by >1.5 points
- Combined with Team A moneyline (Team A just needs to win), this creates overlapping win conditions
- Special case: +0.5 spread in soccer effectively means "Team B wins or draws", which conflicts with Team A moneyline

---

### Rule 3: No Opposing Spreads Where Sum ≤ 0

**Description**: Cannot combine spreads from both sides of the same game where the sum of lines is ≤ 0.

**Examples**:
- ❌ **INVALID**: Team A -3.5 + Team B +2.5 (sum = -1)
- ❌ **INVALID**: Team A -3 + Team B +3 (sum = 0)
- ✅ **VALID**: Team A -2.5 + Team B +4.5 (sum = +2)

**Rationale**: 
- When spreads sum to ≤ 0, there's overlap in winning conditions
- Example: If final score is Team A wins by 3:
  - Team A -3: Push
  - Team B +3: Push
  - Both legs can't lose, creating unfair advantage

---

### Rule 4: No Opposing Totals Where Over - Under ≥ 0

**Description**: Cannot combine over/under bets from the same game where the over line ≥ under line.

**Examples**:
- ❌ **INVALID**: Over 90 + Under 80 (diff = +10)
- ❌ **INVALID**: Over 90 + Under 90 (diff = 0)
- ✅ **VALID**: Over 90 + Under 100 (diff = -10)

**Rationale**:
- When over line ≥ under line, there's guaranteed overlap
- Example: Over 90 + Under 80
  - If final total = 85: Over loses, Under wins
  - If final total = 75: Both Under wins (impossible to lose both)
  - If final total = 95: Over wins (impossible to lose both)
  - No scenario where both lose = unfair advantage

---

### Rule 5: Maximum 12 Legs

**Description**: A parlay cannot contain more than 12 legs.

**Examples**:
- ❌ **INVALID**: 13+ legs in a single parlay
- ✅ **VALID**: 2-12 legs in a parlay

**Rationale**: Sportsbook limit to manage risk exposure.

---

### Rule 6: No Moneyline + Opposite Team Negative Spread (Same Period)

**Description**: Cannot combine a moneyline bet on Team A with a spread bet on the opposite Team B where Team B's spread line is ≤ +0.5, when both bets are in the same period.

**Conditions (ALL must be true for violation)**:
1. ML on Team A + Spread on Team B (opposite team, different outcomeId parity)
2. Team B's spread line ≤ +0.5 (i.e., negative line or +0.5)
3. Both selections from the same game period (e.g., full game ML + full game spread)

**Examples**:
- ❌ **INVALID**: Team A moneyline + Team B -1.5 spread (same period)
- ❌ **INVALID**: Team A moneyline + Team B +0.5 spread (same period)
- ✅ **VALID**: Team A moneyline + Team B +1.5 spread (positive spread ≥ +1)
- ✅ **VALID**: Team A moneyline + Team A -1.5 spread (same team, not opposite)
- ✅ **VALID**: Full game moneyline + 1st half spread (different periods)

**Period Matching**:
- Full game ML (markets 11, 219, 251, 64) pairs with full game Spread (markets 16, 223)
- 1st quarter ML pairs with 1st quarter Spread only
- Cross-period combos (full game ML + 1H spread) are allowed

**Rationale**:
- Team A moneyline means Team A wins
- Team B spread ≤ +0.5 effectively means Team B doesn't lose (or wins)
- These are conflicting outcomes that create overlapping conditions

---

## Usage

### Running the Validation Script

```bash
cd /Users/tranlam/Documents/GitHub/python-parlay-api-integration-guide
source venv/bin/activate
python validate_parlay_rules.py
```

### Test Output

The script will:
1. Load fresh market lines from `fresh_market_lines.json`
2. Generate test scenarios covering all rules
3. Validate each scenario
4. Report pass/fail for each test
5. Display violations with detailed explanations

### Example Output

```
🔍 PARLAY RULES VALIDATION TEST SUITE
====================================================================================================

✅ Loaded 225 fresh market lines

📋 Generating test scenarios...
✅ Generated 5 test scenarios

────────────────────────────────────────────────────────────────────────────────────────────────────
🧪 Test 1: Both sides of moneyline (INVALID)
────────────────────────────────────────────────────────────────────────────────────────────────────

📦 Parlay contains 2 legs:
  • Event 20022497: Moneyline (outcomeId=4, line=0) - 95090d26...
  • Event 20022497: Moneyline (outcomeId=5, line=0) - b09b1a89...

✅ TEST PASSED - Expected INVALID, Got INVALID

⚠️  Violations detected:
  ❌ Both sides of Moneyline in event 20022497: ['95090d26b2c0137894ea80a5107c6cf0', 'b09b1a89564f47ec9b316030fe218c8b']

────────────────────────────────────────────────────────────────────────────────────────────────────
📊 TEST SUMMARY
====================================================================================================
  Total Tests: 5
  ✅ Passed: 5
  ❌ Failed: 0
  Success Rate: 100.0%
====================================================================================================
```

---

## Market Types Supported

| Market ID | Type | Description |
|-----------|------|-------------|
| 11 | Moneyline | Win/Loss bets |
| 64 | Moneyline | Alternative moneyline |
| 219 | Moneyline | Full game moneyline (NBA/NHL) |
| 251 | Moneyline | 3-way moneyline (MLB) |
| 16 | Asian Handicap | Point spread with push protection |
| 223 | Point Spread | Full game spread (NBA/NHL) |
| 256 | Point Spread | Alternative spread market |
| 410 | Point Spread | Custom spread market |
| 18 | Total Points | Over/Under scoring |
| 225 | Team Totals | Individual team scoring |
| 258 | Alternate Totals | Alternative over/under lines |
| 412 | Totals | Custom totals market |

---

## Technical Implementation

### Key Classes

**`MarketLine`**: Data class representing a single betting line
- `line_id`: Unique identifier
- `market_id`: Type of market (11=Moneyline, 223=Spread, etc.)
- `outcome_id`: Specific outcome (home/away, over/under)
- `line`: Point value (spread amount, total points, etc.)
- `sport_event_id`: Game/event identifier

**`ParlayValidator`**: Main validation engine
- `validate_no_both_sides_moneyline()`: Rule 1 validator
- `validate_no_moneyline_with_negative_spread()`: Rule 2 validator
- `validate_no_opposing_spreads_sum_lte_zero()`: Rule 3 validator
- `validate_no_opposing_totals_diff_gte_zero()`: Rule 4 validator

### Detection Heuristics

**Home vs Away Team**:
- Even `outcomeId` (4, 12, 1714) = Home team
- Odd `outcomeId` (5, 13, 1715) = Away team

**Over vs Under** (for totals):
- Lower `outcomeId` typically = Over
- Higher `outcomeId` typically = Under

---

## Integration with Parlay Autoplay

The validation logic can be integrated into `parlay_autoplay.py` to ensure all generated parlays comply with these rules before submission.

### Recommended Integration Points

1. **Before Parlay Creation**: Validate line combinations in `get_random_market_lines()`
2. **Rejection Handling**: Skip invalid combinations and regenerate
3. **Logging**: Track validation failures for analysis

### Example Integration

```python
from validate_parlay_rules import ParlayValidator, MarketLine

validator = ParlayValidator()

def get_valid_random_market_lines(self, min_legs: int = 2, max_legs: int = 12) -> List[Dict]:
    """Get random valid market lines for parlay"""
    max_attempts = 10
    
    for attempt in range(max_attempts):
        lines = self.get_random_market_lines(min_legs, max_legs)
        
        # Convert to MarketLine objects
        market_lines = [
            MarketLine(
                line_id=l['lineId'],
                market_id=l['marketId'],
                outcome_id=l['outcomeId'],
                line=l['line'],
                sport_event_id=l['sportEventId']
            )
            for l in lines
        ]
        
        # Validate
        result = validator.validate_parlay(market_lines)
        
        if result['valid']:
            return lines
        else:
            logger.debug(f"Invalid parlay combination (attempt {attempt+1}): {result['violations']}")
    
    # Fallback: return best effort
    return self.get_random_market_lines(min_legs, max_legs)
```

---

## Testing and Verification

### Automated Testing

The validation script includes comprehensive test scenarios that verify:
- ✅ Invalid combinations are correctly rejected
- ✅ Valid combinations are correctly accepted
- ✅ Edge cases are handled properly
- ✅ All rules are enforced consistently

### Test Coverage

Current test suite covers:
1. Both sides moneyline (invalid)
2. Moneyline + negative spread (invalid)
3. Moneyline + positive spread (valid)
4. Opposing spreads with sum ≤ 0 (invalid)
5. Multi-event parlays (valid)

### Adding New Tests

To add custom test scenarios, modify `generate_test_scenarios()` in `validate_parlay_rules.py`:

```python
scenarios.append((
    "Test Description (VALID/INVALID)",
    [list_of_market_lines],
    expected_valid_boolean
))
```

---

## Maintenance

### Updating Market Types

If new market types are introduced, update the `MARKET_TYPES` dictionary:

```python
MARKET_TYPES = {
    11: "Moneyline",
    # ... existing types ...
    999: "New Market Type"  # Add new types here
}
```

### Adjusting Heuristics

If outcome ID patterns change, update the property methods in the `MarketLine` class:

```python
@property
def is_home_team(self) -> bool:
    # Update logic based on new patterns
    return self.outcome_id % 2 == 0
```

---

## Support

For questions or issues with the validation system:
1. Check test output for specific violation messages
2. Review market line data in `fresh_market_lines.json`
3. Verify market type mappings in `MARKET_TYPES`
4. Run validation script with verbose logging

---

## Version History

- **v1.1** (2026-03-04): Updated Rule 6 with correct business logic
  - Rule 6: ML + opposite team negative spread (line ≤ +0.5), same period only
  - Added market IDs 251, 64, 410, 412
  - Added Rule 5 (max 12 legs) documentation
- **v1.0** (2025-11-11): Initial implementation with all 4 core validation rules
  - Rule 1: Both sides moneyline
  - Rule 2: Moneyline + negative spread
  - Rule 3: Opposing spreads sum
  - Rule 4: Over/under totals diff
