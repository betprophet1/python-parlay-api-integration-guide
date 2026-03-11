# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Python Parlay API Integration Guide** - a real-time sports betting system that integrates with parlay betting APIs. It acts as a sophisticated betting engine that receives parlay quote requests, calculates odds, and provides pricing for multi-leg sports bets in real-time.

### Key Business Logic
- **Parlay Betting**: Combines multiple individual bets where all legs must win for payout
- **Real-time Pricing**: Provides instant odds calculation for complex multi-leg bets  
- **Market Integration**: Supports NBA, NHL, MLB, College Basketball and other sports
- **WebSocket Communication**: Real-time bidirectional communication for live betting feeds
- **Risk Management**: Built-in exposure monitoring and configurable risk limits

## Common Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Main application entry point
python src/main.py
```

### Configuration
```bash
# Edit API credentials (required before first run)
# Configure tournaments of interest and API keys
nano src/user_info.json

# For staging environment, use staging configuration
nano src/user_info_staging.json
```

## Architecture Overview

### Core Components Architecture
The application follows a **event-driven, real-time trading architecture**:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   main.py       │───▶│ parlay_connect.py │◀──▶│ WebSocket APIs  │
│ (Entry Point)   │    │ (Core Engine)     │    │ (Live Data)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   config.py     │    │   constants.py   │    │ Market Data     │
│ (Configuration) │    │ (Valid Odds)     │    │ (Real-time)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### System Workflow Architecture
The application operates in **two distinct phases**:

#### 1. Initialization Phase
- Authentication with betting API
- Account balance verification
- Tournament and market data seeding
- WebSocket connection establishment
- Supported betting lines registration

#### 2. Live Trading Phase
- Real-time parlay quote request processing
- Odds calculation and risk assessment
- Price quote response generation
- Price confirmation handling
- Continuous health monitoring

### Key Classes and Responsibilities

#### `ParlayInteractions` (parlay_connect.py)
The **central trading engine** that handles:
- **Authentication**: JWT token management with auto-refresh
- **Market Data**: Tournament/event seeding and validation
- **WebSocket Management**: Real-time connection handling
- **Quote Processing**: Parlay request processing and pricing
- **Risk Management**: Exposure monitoring and limit enforcement

### Data Flow Architecture

```
Parlay Quote Request (WebSocket)
            │
            ▼
Extract parlay details (ID, stake, market lines)
            │
            ▼
Risk assessment & odds calculation
            │
            ▼
Generate multiple pricing offers (different risk/reward tiers)
            │
            ▼
Send price quote response
            │
            ▼
Handle price confirmation (accept/reject)
```

### Configuration Architecture

#### Environment Configuration
- `user_info.json` - Production API credentials and tournament selection
- `user_info_staging.json` - Staging environment configuration
- `config.py` - Base URLs, endpoints, and environment loading

#### Tournament Selection Strategy
The system supports **selective tournament loading** to optimize performance:
- Configure specific tournaments in `tournaments` array
- Set `load_all_tournaments: false` for selective loading
- Market data is loaded only for specified tournaments

### WebSocket Event Architecture

#### Public Channel Events
- **`price.ask.new`**: Receives parlay quoting requests
- Broadcasts to all connected trading engines

#### Private Channel Events  
- **`price.confirm.new`**: Receives price confirmation requests
- **Health checks**: System availability monitoring

### Risk Management Architecture

The system implements **multi-tier risk management**:

#### Quote Structure
```json
{
  "offers": [
    {
      "odds": 100000,      // High odds, low risk
      "max_risk": 200,     // Maximum $200 exposure
      "valid_until": "timestamp"
    },
    {
      "odds": 800,         // Lower odds, higher risk
      "max_risk": 2000,    // Maximum $2000 exposure  
      "valid_until": "timestamp"
    }
  ]
}
```

## Important Configuration Details

### API Credentials Structure
```json
{
  "access_key": "your_access_key",
  "secret_key": "your_secret_key", 
  "tournaments": ["NBA", "NHL", "MLB", "College Basketball"],
  "load_all_tournaments": false
}
```

### Supported Market Types
| Market ID | Type | Description |
|-----------|------|-------------|
| 11 | Moneyline | Win/Loss bets |
| 16 | Asian Handicap | Point spread with push protection |
| 18 | Total Points | Over/Under scoring |
| 225 | Team Totals | Individual team scoring |
| 256 | Point Spread | Traditional spread betting |
| 258 | Alternate Totals | Alternative over/under lines |

### Logging and Monitoring
- All activities logged with emoji indicators for easy identification
- Real-time system health monitoring via WebSocket
- Structured error handling with detailed context
- Account balance monitoring and exposure tracking

## Development Notes

### Authentication Flow
The system uses **JWT bearer token authentication** with automatic refresh. Tokens are managed transparently by the `ParlayInteractions` class.

### Market Data Validation
Comprehensive validation ensures all market data has:
- Valid line IDs for all selections
- Complete market structures
- Proper tournament/event relationships

### Error Handling Strategy
- **Graceful degradation**: System continues with cached data on API failures
- **Automatic reconnection**: WebSocket connections auto-recover
- **Comprehensive logging**: All errors logged with context for debugging

### Performance Considerations
- **Selective loading**: Only load tournaments of interest
- **Efficient WebSocket management**: Single connection for all real-time data
- **Optimized quote generation**: Pre-calculated odds structures for fast response