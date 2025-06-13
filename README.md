# 🎰 Python Parlay API Integration Guide

## Overview

This Python application provides a real-time sports betting system that integrates with parlay betting APIs. It acts as a sophisticated betting engine that receives parlay quote requests, calculates odds, and provides pricing for multi-leg sports bets in real-time.

## 🚀 Key Features

- **Real-time WebSocket Integration**: Connects to live betting feeds
- **Multi-Sport Support**: Handles NBA, NHL, MLB, College Basketball, and more
- **Automated Parlay Pricing**: Calculates and provides odds for complex multi-leg bets
- **Health Monitoring**: Built-in system health checks and monitoring
- **Session Management**: Automatic token refresh and connection management
- **Market Data Seeding**: Loads and validates sports events and betting markets

## 🎲 How Parlay Betting Works

### What is a Parlay?
A parlay is a single bet that combines multiple individual bets (called "legs"). **All legs must win for the parlay to pay out**, but the potential payout is much higher than individual bets.

### Example Parlay:
```
🏀 Lakers vs Warriors - Lakers -5.5 points
⚾ Yankees vs Red Sox - Over 8.5 total runs  
🏒 Bruins vs Rangers - Bruins Moneyline
```
**Result**: All three must win for the parlay to win.

## 🔄 System Workflow

### 1. **Initialization Phase**
```
🔧 Initialize System
🔑 Authenticate with API
💰 Fetch Account Balance
🌱 Seed Tournaments & Markets
📡 Establish WebSocket Connections
📋 Send Supported Betting Lines
```

### 2. **Live Trading Phase**
```
📈 Receive Parlay Quote Request
🎲 Extract Parlay Details (ID, Stake, Market Lines)
📊 Calculate Odds & Risk Assessment
🚀 Send Price Quote Response
✅ Handle Price Confirmations
💚 Monitor System Health
```

## 📋 Parlay Request Structure

When the system receives a parlay quote request, it contains:

```json
{
  "parlay_id": "abc123-def456-789",
  "stake": 50.00,
  "callback_url": "https://api.example.com/parlay/offers",
  "market_lines": [
    {
      "line_id": "line123",
      "market_id": 256,
      "outcome_id": 1714,
      "sport_event_id": 90087682,
      "line": -5.5
    },
    {
      "line_id": "line456", 
      "market_id": 225,
      "outcome_id": 13,
      "sport_event_id": 20022393,
      "line": 8.5
    }
  ]
}
```

## 🎯 How the Script Places/Prices Parlays

### Step 1: Receive Request
- System receives parlay quote request via WebSocket
- Extracts parlay details (stake amount, betting lines, event IDs)
- Logs formatted request details with emojis for clarity

### Step 2: Risk Assessment
- Analyzes each leg of the parlay
- Calculates combined risk exposure
- Determines maximum acceptable stake

### Step 3: Odds Calculation
- Provides multiple pricing options:
  ```python
  offers = [
    {
      'odds': 100000,     # 1000:1 odds
      'max_risk': 200,    # Maximum $200 risk
      'valid_until': timestamp
    },
    {
      'odds': 800,        # 8:1 odds  
      'max_risk': 2000,   # Maximum $2000 risk
      'valid_until': timestamp
    }
  ]
  ```

### Step 4: Response
- Sends pricing back to the requesting system
- Includes multiple betting options
- Sets expiration time for quotes (5+ seconds)

### Step 5: Confirmation Handling
- If bettor accepts a quote, receives confirmation request
- Validates the accepted odds
- Confirms or rejects the bet placement
- Updates risk management systems

## 🛠 Installation & Setup

### Prerequisites
- Python 3.7+
- Virtual environment support
- Network access to betting APIs

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd python-parlay-api-integration-guide
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure credentials**
   - Edit `src/user_info.json` with your API credentials:
   ```json
   {
     "access_key": "your_access_key",
     "secret_key": "your_secret_key",
     "tournaments": ["NBA", "NHL", "MLB"],
     "load_all_tournaments": false
   }
   ```

5. **Run the application**
   ```bash
   python src/main.py
   ```

## 📊 Live Output Example

```
🕐 14:32:15 | INFO | 📈 PRICE QUOTE REQUEST RECEIVED
🕐 14:32:15 | INFO | 🎲 Parlay ID: f71276fe-6a30-41d3-b366
🕐 14:32:15 | INFO | 💰 Stake Amount: $6.08
🕐 14:32:15 | INFO | 📊 Number of Lines: 2
🕐 14:32:15 | INFO | 📋 Market Lines:
🕐 14:32:15 | INFO |   1. Line ID: 411806b5...
🕐 14:32:15 | INFO |      Market: 223 | Outcome: 1714
🕐 14:32:15 | INFO |      Event: 13001947 | Line: 11.5
🕐 14:32:15 | INFO |   2. Line ID: aec173dd...
🕐 14:32:15 | INFO |      Market: 225 | Outcome: 13  
🕐 14:32:15 | INFO |      Event: 20022393 | Line: 230.5
🕐 14:32:15 | INFO | 🚀 Price quote sent successfully!
```

## 🔧 Configuration

### Tournament Selection
Edit `src/user_info.json` to specify which sports/tournaments to monitor:
```json
{
  "tournaments": ["NBA", "College Basketball", "NHL", "MLB"],
  "load_all_tournaments": false
}
```

### API Endpoints
Main endpoints are configured in `src/config.py`:
- Authentication: `/partner/auth/login`
- Market data: `/partner/mm/get_markets`
- WebSocket config: `/parlay/sp/websocket/connection-config`
- Pricing callback: `/parlay/sp/orders/offers`

## 🎮 Market Types Supported

| Market ID | Type | Description |
|-----------|------|-------------|
| 11 | Moneyline | Win/Loss bets |
| 16 | Asian Handicap | Point spread with push protection |
| 18 | Total Points | Over/Under scoring |
| 225 | Team Totals | Individual team scoring |
| 256 | Point Spread | Traditional spread betting |
| 258 | Alternate Totals | Alternative over/under lines |

## 🔐 Security Features

- **JWT Token Management**: Automatic token refresh
- **Secure WebSocket**: Authenticated real-time connections  
- **Rate Limiting**: Built-in request throttling
- **Error Handling**: Comprehensive exception management
- **Health Monitoring**: Continuous system health checks

## 📈 Risk Management

- **Maximum Risk Limits**: Configurable per-parlay risk caps
- **Exposure Monitoring**: Real-time position tracking
- **Quote Expiration**: Time-limited pricing windows
- **Multiple Pricing Tiers**: Different risk/reward options

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **API Authentication**: Verify credentials in `user_info.json`
3. **WebSocket Disconnection**: System auto-reconnects on failure
4. **Market Data Missing**: Check tournament configuration

### Logs Location
All activity is logged to console with timestamp and emoji indicators for easy monitoring.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and development purposes. Always comply with local gambling laws and regulations. Use responsibly and never bet more than you can afford to lose.

---

**🎯 Ready to start? Run `python src/main.py` and watch the real-time parlay betting system come to life!**

