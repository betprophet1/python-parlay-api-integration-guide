# 🎰 Parlay Autoplay - Load Testing System

Automated parlay load testing system with multiple testing modes for comprehensive API stress testing.

## 📁 Repository Structure

```
python-parlay-api-integration-guide/
├── parlay_autoplay.py          # Main autoplay script (START HERE)
├── fresh_market_lines.json     # Fresh line IDs for testing
├── utils/                      # Utility scripts
│   ├── fetch_market_lines.py  # Fetch fresh market data
│   ├── parlay_status_checker.py
│   ├── sp_order_checker.py
│   └── get_user_token.py
├── archived_tests/             # Old test scripts (archived)
└── src/                        # Original parlay integration code

```

## 🚀 Quick Start

### 1. Generate Fresh Market Lines

Before running tests, fetch fresh market line IDs:

```bash
python utils/fetch_market_lines.py
```

This creates `fresh_market_lines.json` with current valid betting lines.

### 2. Run Load Tests

#### Normal Mode (Sequential Testing)
```bash
# 10 tests with 1 second delay
python parlay_autoplay.py --mode normal --iterations 10 --delay 1
```

#### Continuous Mode (Run Until Interrupted)
```bash
# Non-stop testing with 0.5s delay
python parlay_autoplay.py --mode continuous --delay 0.5

# Press Ctrl+C to stop gracefully
```

#### Aggressive Mode (Concurrent Load Testing)
```bash
# 20 iterations with 5 concurrent threads = 100 total tests
python parlay_autoplay.py --mode aggressive --iterations 20 --concurrency 5

# Extreme load test: 100 iterations × 10 threads = 1000 tests
python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 10 --delay 0
```

## 📊 Testing Modes

### 🎯 Normal Mode
- Sequential test execution
- Configurable delay between tests
- Ideal for baseline performance testing
- Low server load

### 🔄 Continuous Mode
- Runs indefinitely until interrupted (Ctrl+C)
- Live statistics every 10 tests
- Great for long-running stability tests
- Monitors throughput and success rates

### ⚡ Aggressive Mode
- Concurrent multi-threaded execution
- Configurable thread concurrency (1-20+)
- High-load stress testing
- Real-world traffic simulation

## 🎲 Features

### Dynamic Parlay Generation
- Random 2-12 leg parlays
- Unique event validation (no duplicates)
- Shuffled line selection per test
- Fresh market data integration

### Performance Metrics
- Success/failure rates
- Response time breakdown (auth, create, offer)
- Throughput (tests/minute)
- Leg count distribution
- Error analysis

### Smart Error Handling
- Graceful shutdown (Ctrl+C)
- Thread-safe operations
- Comprehensive logging
- Detailed failure tracking

## 📋 Command-Line Options

```
--mode {normal,continuous,aggressive}
    Testing mode (default: normal)

--iterations INT
    Number of test iterations (default: 10)
    Ignored in continuous mode

--concurrency INT
    Number of concurrent threads for aggressive mode (default: 1)

--delay FLOAT
    Delay between tests in seconds (default: 1.0)
```

## 📈 Output & Logging

### Console Output
Real-time test results with emojis for easy scanning:
- ✅ Test passed
- ❌ Test failed
- 📊 Live statistics
- 🏁 Final summary

### Log Files
Detailed logs saved to: `parlay_autoplay_{timestamp}.log`

Contains:
- All test results
- Response times
- Error details
- Performance metrics

## 🔧 Configuration

### SP Credentials
Edit credentials in `parlay_autoplay.py`:
```python
self.sp1_credentials = {
    "access_key": "your_key",
    "secret_key": "your_secret"
}
```

### Market Line Endpoints
Edit in `utils/fetch_market_lines.py` to fetch from different events.

## 📖 Example Usage Scenarios

### Quick Smoke Test
```bash
python parlay_autoplay.py --mode normal --iterations 5 --delay 0.5
```

### Sustained Load Test
```bash
python parlay_autoplay.py --mode continuous --delay 1
# Run for 1 hour, then Ctrl+C
```

### Stress Test
```bash
python parlay_autoplay.py --mode aggressive --iterations 50 --concurrency 10
# 500 total tests with 10 concurrent threads
```

### Peak Traffic Simulation
```bash
python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 20 --delay 0
# 2000 concurrent tests, no delay
```

## 📊 Understanding Results

### Success Rate
- **100%**: Perfect, all tests passed
- **>90%**: Good, minor issues
- **<90%**: Investigate failures

### Throughput
- **Normal mode**: 30-60 tests/min
- **Continuous mode**: 30-60 tests/min
- **Aggressive mode**: 100-500+ tests/min (depending on concurrency)

### Response Times
- **Auth**: 0.5-1.0s (normal)
- **Create Parlay**: 0.6-0.9s (normal)
- **SP Offer**: 0.6-0.8s (normal)

## 🐛 Troubleshooting

### No market lines error
```bash
python utils/fetch_market_lines.py
```

### High failure rate
- Check market line freshness
- Verify SP credentials
- Check API status
- Review error logs

### Slow performance
- Reduce concurrency
- Increase delay
- Check network connection
- Verify API health

## 🛠️ Utility Scripts

Located in `utils/` directory:

- **fetch_market_lines.py**: Generate fresh betting lines
- **parlay_status_checker.py**: Check parlay order status
- **sp_order_checker.py**: Check SP orders
- **get_user_token.py**: Get auth token
- **find_active_events.py**: Find active events for testing

## 📝 Notes

- Tests use sandbox environment by default
- Each parlay has random 2-12 legs
- Duplicate events automatically prevented
- Graceful shutdown preserves results
- Logs saved for all sessions

## 🎯 Best Practices

1. **Start Small**: Begin with normal mode, few iterations
2. **Fresh Lines**: Update market lines daily
3. **Monitor Logs**: Check logs for detailed errors
4. **Gradual Load**: Increase concurrency gradually
5. **Interruption**: Use Ctrl+C for clean shutdown

---

**Happy Load Testing! 🚀**
