# Comprehensive E2E Test Coverage Summary

## Overview
Expanded E2E test suite with **9 comprehensive test cases** covering all scenarios from unit tests, now running against live API.

## Test Suite: `test_e2e_odds_validation.py`

### Test Cases

#### ✅ **Valid Positive Odds Tests**

**Test 1: Valid +377 (Requirement Example)**
- **Odds**: +377
- **Probabilities**: [0.8161, 0.2570]
- **Expected**: Combined prob: 0.2097 → odds: +377, range: [370, 380] ✓
- **Validation**: Should PASS

**Test 2: Valid +300 (Simple 2-leg)**
- **Odds**: +300
- **Probabilities**: [0.5, 0.5]
- **Expected**: Combined prob: 0.25 → odds: +300, exact match ✓
- **Validation**: Should PASS

**Test 3: Valid +700 (3-leg parlay)**
- **Odds**: +700
- **Probabilities**: [0.5, 0.5, 0.5]
- **Expected**: Combined prob: 0.125 → odds: +700, exact match ✓
- **Validation**: Should PASS

---

#### ✅ **Valid Negative Odds Tests**

**Test 4: Valid -200 (Heavy favorite)**
- **Odds**: -200
- **Probabilities**: [0.8, 0.833]
- **Expected**: Combined prob: 0.6664 → odds: -200, range: [-200, -198] ✓
- **Validation**: Should PASS

**Test 6: Valid -112 (Favorite 2-leg)**
- **Odds**: -112
- **Probabilities**: [0.73, 0.7237]
- **Expected**: Combined prob: 0.5283 → odds: -112, range: [-112, -111] ✓
- **Validation**: Should PASS

---

#### ❌ **Invalid - Edge Cases**

**Test 5: Invalid -110 (Edge case - calculated -111)**
- **Odds**: -110
- **Probabilities**: [0.7, 0.75]
- **Expected**: Combined prob: 0.525 → odds: -111, outside [-110, -109] ✗
- **Validation**: Should FAIL (correctly)

---

#### ❌ **Invalid - Mismatch Tests**

**Test 7: Invalid -150 (Negative vs Positive mismatch)**
- **Odds**: -150 (negative)
- **Probabilities**: [0.6, 0.56]
- **Expected**: Combined prob: 0.336 → odds: +198 (positive), doesn't match -150 ✗
- **Validation**: Should FAIL (correctly)

**Test 8: Invalid +500 (Positive mismatch)**
- **Odds**: +500 (positive)
- **Probabilities**: [0.8, 0.8]
- **Expected**: Combined prob: 0.64 → odds: -178 (negative), doesn't match +500 ✗
- **Validation**: Should FAIL (correctly)

**Test 9: Invalid -150 (Large negative mismatch)**
- **Odds**: -150
- **Probabilities**: [0.9, 0.9]
- **Expected**: Combined prob: 0.81 → odds: -426, doesn't match -150 ✗
- **Validation**: Should FAIL (correctly)

---

## Coverage Matrix

| Test # | Type | Odds | Legs | Validation | Pass/Fail | Category |
|--------|------|------|------|------------|-----------|----------|
| 1 | Valid | +377 | 2 | VALID | ✅ PASS | Positive - From Requirement |
| 2 | Valid | +300 | 2 | VALID | ✅ PASS | Positive - Simple |
| 3 | Valid | +700 | 3 | VALID | ✅ PASS | Positive - Multi-leg |
| 4 | Valid | -200 | 2 | VALID | ✅ PASS | Negative - Heavy Favorite |
| 5 | Invalid | -110 | 2 | INVALID | ✅ PASS | Negative - Edge Case |
| 6 | Valid | -112 | 2 | VALID | ✅ PASS | Negative - Moderate Favorite |
| 7 | Invalid | -150 | 2 | INVALID | ✅ PASS | Sign Mismatch (Neg vs Pos) |
| 8 | Invalid | +500 | 2 | INVALID | ✅ PASS | Sign Mismatch (Pos vs Neg) |
| 9 | Invalid | -150 | 2 | INVALID | ✅ PASS | Large Mismatch |

## Test Categories

### 1. **Positive Odds Coverage** (Tests 1-3)
- ✅ Requirement example (+377)
- ✅ Simple 2-leg (+300)
- ✅ Multi-leg parlay (+700)

### 2. **Negative Odds Coverage** (Tests 4, 6)
- ✅ Heavy favorites (-200)
- ✅ Moderate favorites (-112)

### 3. **Edge Cases** (Test 5)
- ✅ Boundary conditions (-110 vs -111)

### 4. **Mismatch Detection** (Tests 7-9)
- ✅ Negative vs positive sign mismatch
- ✅ Positive vs negative sign mismatch
- ✅ Large magnitude mismatches

## How to Run

### Run All Tests
```bash
python test_e2e_odds_validation.py
```

### Run Specific Test
Edit the `test_configs` list in the file to include only the tests you want.

### View Detailed Output
The test provides:
- ✅ Raw HTTP requests for every API call
- ✅ Complete response bodies
- ✅ Detailed odds validation checks
- ✅ Pass/fail status for each test

## Expected Results

### Successful Test Run Should Show:
```
🎉 ALL E2E TESTS PASSED!
✓ Test 1: Valid +377 - PASS
✓ Test 2: Valid +300 - PASS
✓ Test 3: Valid +700 - PASS
✓ Test 4: Valid -200 - PASS
✓ Test 5: Invalid -110 - PASS (correctly detected invalid)
✓ Test 6: Valid -112 - PASS
✓ Test 7: Invalid -150 - PASS (correctly detected invalid)
✓ Test 8: Invalid +500 - PASS (correctly detected invalid)
✓ Test 9: Invalid -150 - PASS (correctly detected invalid)

📊 Total: 9/9 tests passed
```

## Key Validation Scenarios Tested

### ✅ **Range Validation**
- Tests validate that calculated odds fall within adjacent ladder points
- Example: +377 must be in range [370, 380]

### ✅ **Sign Matching**
- Positive odds must match positive calculated odds
- Negative odds must match negative calculated odds

### ✅ **Multi-leg Parlays**
- 2-leg parlays: Tests 1, 2, 4-9
- 3-leg parlays: Test 3
- Probability multiplication: prob1 × prob2 × prob3

### ✅ **Edge Cases**
- Boundary conditions at ladder steps
- Exact matches vs near matches
- Large mismatches

## Integration Points

Each test exercises the complete flow:
1. **User Authentication** → Get user token
2. **SP Authentication** → Get SP token
3. **Create Parlay** → POST /user/request
4. **SP Quote** → POST /sp/orders/offers (with estimated_prices)
5. **User Confirm** → POST /user/confirm
6. **Get Order** → GET /sp/orders (find order_uuid)
7. **Odds Validation** → `validate_price_probability()` ✨
8. **SP Confirmation** → POST /sp/orders/confirmations (with price_probability)

## Benefits

✅ **Comprehensive Coverage**: All unit test scenarios now run E2E
✅ **Real API Testing**: Tests against actual sandbox environment
✅ **Full Request/Response Logging**: Complete visibility into API interactions
✅ **Validation Integration**: Shows odds validation in real parlay flow
✅ **Production Ready**: Validates the system works end-to-end

## Notes

- Tests may fail if orders are already processed (status != 'sent_confirmation')
- Run tests against fresh parlay requests for best results
- The 2-second wait between user confirm and getting orders allows system to process
- All tests include detailed logging for debugging
