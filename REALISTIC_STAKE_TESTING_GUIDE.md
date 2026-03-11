# Realistic Stake Testing Guide

This guide explains how to use the new realistic stake testing suite that implements proper SP offer calculations for parlay confirmations.

## 🎯 **Key Discovery**

Based on your observation (`p_id: 0199bee6-f989-7bca-9487-26e30c7ff494`), we discovered the stake calculation formula:

```
Available Stake = max_risk ÷ decimal_odds
```

**Your Example:**
- Odds: +800 → decimal odds: 9.0
- Available Stake: $12.50  
- To Win: $100.00
- **SP max_risk**: $112.50 (calculated backwards)

## 📁 **New Test Files Created**

### 1. **Stake Calculation Analysis**
- `analyze_stake_calculation.py` - Validates the discovered formula
- Run: `python analyze_stake_calculation.py`

### 2. **Scenario Generation**
- `generate_stake_scenarios.py` - Creates 10 realistic test scenarios
- `realistic_stake_scenarios.json` - Generated test data (auto-created)
- Run: `python generate_stake_scenarios.py`

### 3. **Test Suites**
- `test_realistic_stake_confirmations.py` - Basic realistic stake tests
- `test_advanced_parlay_confirmations.py` - Comprehensive scenario-based tests
- Run: `python test_advanced_parlay_confirmations.py`

## 🚀 **Quick Start Guide**

### Step 1: Generate Test Scenarios
```bash
python generate_stake_scenarios.py
```
This creates `realistic_stake_scenarios.json` with 10 comprehensive test scenarios.

### Step 2: Update Authentication
Update these files with your real credentials:
- `test_realistic_stake_confirmations.py`
- `test_advanced_parlay_confirmations.py`

```python
# Update these values
USER_TOKEN = "your_fresh_user_token_here"
SP1_ACCESS_KEY = "your_sp1_access_key"
SP1_SECRET_KEY = "your_sp1_secret_key"
SP2_ACCESS_KEY = "your_sp2_access_key" 
SP2_SECRET_KEY = "your_sp2_secret_key"
```

### Step 3: Run Advanced Tests
```bash
python test_advanced_parlay_confirmations.py
```

## 📊 **Test Scenarios Generated**

| Scenario | Description | Odds | Available Stake | User Confirms |
|----------|-------------|------|-----------------|---------------|
| 1 | Your Original Example | +800 | $25.00 | $12.50 (50%) |
| 2 | Low Odds High Stakes | +150 | $390.00 | $234.00 (60%) |
| 3 | High Odds Low Stakes | +1200 | $35.00 | $35.00 (100%) |
| 4 | Mixed Odds Selection | +900 | $27.00 | $21.60 (80%) |
| 5 | Favorite Lines | -105 | $102.44 | $71.71 (70%) |
| 6 | Even Money | +105 | $153.66 | $138.29 (90%) |
| 7 | Extreme Long Shot | +2500 | $30.00 | $30.00 (100%) |
| 8 | Heavy Favorite | -280 | $128.95 | $103.16 (80%) |
| 9 | High Liquidity (4 SPs) | +500 | $112.50 | $67.50 (60%) |
| 10 | Multi-Tier Required | +400 | $70.00 | $70.00 (100%) |

## 🔧 **Key Features**

### **Realistic Stake Calculations**
- Uses actual formula: `Available Stake = max_risk ÷ decimal_odds`
- Tests various odds ranges: -300 to +2500
- Covers micro stakes ($10) to high stakes ($390)

### **Multi-SP Scenarios**
- Same odds blending (SP1 + SP2 with +800 odds)
- Different odds selection (system picks best)
- High liquidity scenarios (4 SPs)

### **User Confirmation Testing**
- Full confirmation (100% of available)
- Partial confirmations (50-90%)
- Realistic user behavior simulation

### **Complete API Integration**
- Real authentication with SPs
- Actual parlay creation
- Live offer submission
- User confirmation via `/parlay/api/v1/user/confirm`

## 📋 **Sample Test Output**

```
🧪 RUNNING SCENARIO: User's Original Example Replicated
================================================================================
📝 Description: Replicate user's observation: +800 odds, $12.50 stake, $100 payout
🎯 Expected: Should match exactly: $12.50 stake → $100 payout

💰 SP1 providing offer:
   Odds: +800
   Max Risk: $112.50
   Expected Available Stake: $12.50

💰 SP2 providing offer:
   Odds: +800
   Max Risk: $112.50
   Expected Available Stake: $12.50

✅ User confirming parlay based on scenario:
   Scenario: User's Original Example Replicated
   Best Odds: +800
   Total Available: $25.00
   Confirmation Stake: $12.50
   Expected Payout: $100.00
   Confirmation Ratio: 50%

✅ SCENARIO PASSED: User's Original Example Replicated
```

## 🎯 **Testing Coverage**

### **Odds Ranges**
- **Extreme long shots**: +2500 (tiny stakes)
- **High odds**: +800, +900, +1200
- **Medium odds**: +400, +500  
- **Low odds**: +150 (high stakes)
- **Even money**: +100, +105
- **Favorites**: -105, -110
- **Heavy favorites**: -280, -300

### **Confirmation Patterns**
- **Conservative users**: 50-60% confirmation
- **Moderate users**: 70-80% confirmation
- **Aggressive users**: 90-100% confirmation

### **Multi-SP Scenarios**
- **Liquidity blending**: Multiple SPs same odds
- **Best selection**: System picks highest odds
- **Tier matching**: Large stakes requiring multiple SPs

## ⚠️ **Important Notes**

### **Token Management**
- User tokens expire regularly - update before testing
- SP tokens are usually longer-lasting
- Test with fresh tokens for accurate results

### **API Endpoint**
- All tests target: `https://parlay-api-staging.herokuapp.com`
- Primary endpoint: `/parlay/api/v1/user/confirm`
- Uses realistic `stake_cents` values

### **Validation**
- Tests confirm `stake_cents ≤ total_available_stake_cents`  
- Validates SP risk exposure: `payout ≤ max_risk`
- Checks multi-SP blending logic

## 🔍 **Understanding Results**

### **Success Indicators**
- ✅ SP authentication successful
- ✅ Parlay creation successful  
- ✅ SP offers submitted successfully
- ✅ User confirmation processed successfully

### **Common Issues**
- ❌ 401 Unauthorized → Token expired
- ❌ 400 Bad Request → Invalid stake amount or line IDs
- ❌ 404 Not Found → Parlay ID not found

## 🚀 **Next Steps**

1. **Run with Fresh Tokens**: Update all tokens and run tests
2. **Analyze Results**: Check which scenarios pass/fail
3. **Debug Issues**: Use detailed logging for troubleshooting
4. **Extend Tests**: Add more scenarios based on specific needs
5. **Integration**: Use realistic stakes in your main application

This testing suite provides comprehensive coverage of realistic parlay confirmation scenarios with proper stake calculations! 🎉