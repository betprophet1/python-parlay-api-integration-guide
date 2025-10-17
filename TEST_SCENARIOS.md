# 🧪 Parlay Matching Flow Test Scenarios

## Overview

This document outlines comprehensive test scenarios for the **New Parlay Matching Flow** requirements, including the critical **expired odds scenario** where matching STOPS if SP-provided `valid_until` expires after user placement in FE.

## 📋 New Requirements Summary

### Key Changes
1. **Tiered Matching**: Process best odds first, then proceed tier by tier
2. **STOP on Rejection**: If any SP rejects in a tier, STOP entire matching process
3. **STOP on Expiry**: If odds expire after user confirms, STOP matching process
4. **No Worse Odds**: Never match with worse odds than user saw in FE
5. **Partial OK**: Acceptable to not match full amount rather than use worse odds

## 🎯 Test Categories

### Category 1: Tiered Matching Flow Tests

#### Test Scenario 1: Best Odds Tier - All Accept Success
- **Setup**: Two SPs provide same best odds (800)
- **Action**: User confirms bet, both SPs accept
- **Expected**: Process continues to next tier if stake not fully matched
- **Validation**: Both SPs process orders successfully

#### Test Scenario 2: Best Odds Tier - One Rejects STOP  
- **Setup**: Two SPs provide same best odds (800)
- **Action**: User confirms, SP1 accepts, SP2 rejects
- **Expected**: STOP matching, cancel all unmatched parts
- **Validation**: No fallback to worse odds, matching terminates

#### Test Scenario 3: Second Tier Matching with STOP
- **Setup**: SP1 best odds (900, limited capacity), SP2 second tier (800)  
- **Action**: User stakes requiring both tiers, SP2 rejects
- **Expected**: STOP at second tier, no third tier processing
- **Validation**: Partial match from SP1 only, rest cancelled

#### Test Scenario 4: Complete Multi-Tier Success
- **Setup**: Multiple tiers with different odds/capacities
- **Action**: User confirms large stake requiring multiple tiers
- **Expected**: Full stake matched across tiers with all acceptances
- **Validation**: Orders processed in correct tier sequence

### Category 2: Expired Odds Scenario Tests

#### Test Scenario 5: Odds Expire Before User Confirmation
- **Setup**: SP provides odds with 1-second validity
- **Action**: User attempts to confirm after 2 seconds
- **Expected**: User receives expired odds error, cannot proceed
- **Validation**: API returns appropriate error response

#### Test Scenario 6: Odds Expire During Matching Process ⚠️ **CRITICAL**
- **Setup**: SP1 short validity (3s), SP2 longer validity (60s)
- **Action**: User confirms quickly, SP1 odds expire during processing
- **Expected**: Matching process STOPS, parlay fails entirely
- **Validation**: System detects expiry, terminates matching

#### Test Scenario 7: Mixed Validity Periods
- **Setup**: SP1 best odds (900) but short validity, SP2 worse odds (750) longer validity
- **Action**: User confirms best odds, SP1 expires during processing
- **Expected**: System STOPS rather than fallback to worse odds
- **Validation**: Maintains requirement of no worse odds matching

### Category 3: Edge Cases and Error Tests

#### Test Scenario 8: No SP Responses
- **Setup**: User creates parlay request
- **Action**: User confirms but no SPs provided offers
- **Expected**: Timeout and fail gracefully
- **Validation**: Appropriate error message and status code

#### Test Scenario 9: All SPs Reject Best Tier
- **Setup**: Multiple SPs provide same best odds
- **Action**: All SPs reject in confirmation phase
- **Expected**: STOP immediately, no fallback
- **Validation**: Complete matching failure, no worse odds attempt

#### Test Scenario 10: Stake Exceeds SP Capacity
- **Setup**: SPs with limited combined capacity (300)
- **Action**: User requests stake beyond capacity (500)
- **Expected**: Partial matching up to available capacity
- **Validation**: Matches 300, doesn't fail entirely

## 🔧 Test Setup Instructions

### Prerequisites
```bash
# Install dependencies
pip install pytest requests

# Configure credentials in test_config.json
# Update SP access keys, secret keys, and user JWT token
```

### Configuration
1. **Update `test_config.json`** with actual credentials:
   ```json
   {
     "service_providers": {
       "sp1": {
         "access_key": "YOUR_ACTUAL_SP1_ACCESS_KEY",
         "secret_key": "YOUR_ACTUAL_SP1_SECRET_KEY"
       },
       "sp2": {
         "access_key": "YOUR_ACTUAL_SP2_ACCESS_KEY", 
         "secret_key": "YOUR_ACTUAL_SP2_SECRET_KEY"
       }
     },
     "user_credentials": {
       "jwt_token": "YOUR_ACTUAL_USER_JWT_TOKEN"
     }
   }
   ```

2. **Update market lines** with valid line IDs from your system

### Running Tests

#### Full Test Suite
```bash
python test_parlay_matching_flow.py
# Run with request response logging for debug purpose. 
python complete_test_with_logging.py
```

#### Individual Test Categories
```bash
# Run only tiered matching tests
pytest test_parlay_matching_flow.py::TestTieredMatchingFlow -v

# Run only expired odds tests  
pytest test_parlay_matching_flow.py::TestExpiredOddsScenario -v

# Run only edge case tests
pytest test_parlay_matching_flow.py::TestEdgeCasesAndErrors -v
```

#### Specific Critical Tests
```bash
# Test the critical expired odds during matching scenario
pytest test_parlay_matching_flow.py::TestExpiredOddsScenario::test_scenario_6_odds_expire_during_matching_process -v

# Test STOP behavior on rejection
pytest test_parlay_matching_flow.py::TestTieredMatchingFlow::test_scenario_2_best_odds_tier_one_rejects_stop -v
```

## 📊 Expected Test Results

### Success Criteria
- **Tiered Processing**: Orders processed in correct odds tier sequence
- **STOP Behavior**: Matching terminates on any tier rejection 
- **Expiry Handling**: System detects and handles expired odds correctly
- **No Degradation**: Never matches with worse odds than user saw
- **Graceful Failures**: Appropriate error handling and user feedback

### Critical Validations
1. **Expired Odds Detection**: System must detect `valid_until` expiry
2. **STOP Implementation**: Matching must halt on rejection/expiry
3. **Tier Ordering**: Best odds processed before worse odds
4. **Partial Matching**: System accepts partial fills over worse odds
5. **Error Responses**: Clear error messages for all failure cases

## 🚨 Critical Test Scenarios

### Priority 1: Expired Odds During Matching
This is the **most critical** test scenario based on your clarification:
- User places bet in FE with valid odds
- SP `valid_until` expires during matching process
- System must **STOP matching** immediately
- No fallback to other SPs or worse odds

### Priority 2: Tier Rejection STOP Logic
- Any SP rejection in a tier must STOP entire process
- No routing to worse odds or other SPs
- Maintain user expectation of odds quality

### Priority 3: Multi-SP Coordination
- Multiple SPs with different odds/capacity
- Correct tier-by-tier processing
- Proper handling of partial fills

## 🔍 Monitoring and Logging

Each test includes comprehensive logging:
- **🧪 TEST**: Test scenario start
- **✅ PASS**: Successful validation  
- **❌ FAIL**: Test failure with details
- **🔍 INFO**: Important state changes
- **⚠️ WARN**: Non-critical issues

Example log output:
```
🧪 TEST: Odds expire during matching process - should STOP
✅ User confirmed bet: odds=800, stake=400
🔍 SP1 confirmation failed as expected: 400
✅ PASS: Matching STOPPED due to expired odds during process
```

## 📝 Test Data Management

### Market Lines
Use valid line IDs from your system:
```python
test_market_lines = [
    {
        "line": -10,
        "lineId": "actual_valid_line_id_1",
        "marketId": 223,
        "outcomeId": 1714,
        "sportEventId": 19141
    }
]
```

### Odds and Timing
Configure realistic values:
```python
# Odds tiers (American format)
BEST_ODDS = 1000      # 10:1
SECOND_TIER = 900     # 9:1  
THIRD_TIER = 800      # 8:1

# Validity periods
SHORT_VALIDITY = 1    # 1 second (will expire)
NORMAL_VALIDITY = 50  # 50 seconds
LONG_VALIDITY = 300   # 5 minutes
```

## 🎯 Success Metrics

### Functional Requirements
- [ ] Tiered matching processes best odds first
- [ ] STOP logic prevents worse odds matching
- [ ] Expired odds detection works correctly  
- [ ] Partial matching preferred over worse odds
- [ ] Error handling provides clear feedback

### Performance Requirements  
- [ ] Odds expiry detection < 100ms
- [ ] STOP decision < 200ms
- [ ] Multi-tier processing < 5s total
- [ ] Error responses < 1s

### Integration Requirements
- [ ] Multiple SP coordination
- [ ] WebSocket event handling  
- [ ] Database state consistency
- [ ] User notification accuracy

---