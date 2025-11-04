# 🚀 Parlay Autoplay - Quick Start

## 📋 Pre-requisites

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Generate fresh market lines (do this first!)
python utils/fetch_market_lines.py
```

## ⚡ Quick Commands

### Normal Testing (Good for getting started)
```bash
# Quick test - 5 parlays
python parlay_autoplay.py --mode normal --iterations 5 --delay 0.5

# Standard test - 10 parlays
python parlay_autoplay.py --mode normal --iterations 10 --delay 1
```

### Continuous Testing (Run until Ctrl+C)
```bash
# Moderate pace
python parlay_autoplay.py --mode continuous --delay 1

# Fast pace
python parlay_autoplay.py --mode continuous --delay 0.5

# Maximum speed
python parlay_autoplay.py --mode continuous --delay 0
```

### Aggressive Testing (Concurrent)
```bash
# Light load - 50 tests (10 iterations × 5 threads)
python parlay_autoplay.py --mode aggressive --iterations 10 --concurrency 5

# Medium load - 100 tests (20 iterations × 5 threads)
python parlay_autoplay.py --mode aggressive --iterations 20 --concurrency 5

# Heavy load - 500 tests (50 iterations × 10 threads)
python parlay_autoplay.py --mode aggressive --iterations 50 --concurrency 10

# Extreme load - 1000 tests (100 iterations × 10 threads)
python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 10

# MAXIMUM STRESS - 2000 tests (100 iterations × 20 threads, no delay)
python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 20 --delay 0
```

## 🎯 Recommended Test Scenarios

### 1. Smoke Test (Quick validation)
```bash
python parlay_autoplay.py --mode normal --iterations 3 --delay 0.5
```
**Duration**: ~10 seconds  
**Use case**: Quick functionality check

### 2. Standard Load Test
```bash
python parlay_autoplay.py --mode aggressive --iterations 20 --concurrency 5
```
**Duration**: ~2-3 minutes  
**Total tests**: 100  
**Use case**: Regular performance testing

### 3. Sustained Stability Test
```bash
python parlay_autoplay.py --mode continuous --delay 1
# Let it run for 30-60 minutes, then Ctrl+C
```
**Duration**: 30-60 minutes  
**Total tests**: ~1800-3600  
**Use case**: Long-running stability check

### 4. Peak Traffic Simulation
```bash
python parlay_autoplay.py --mode aggressive --iterations 50 --concurrency 10 --delay 0
```
**Duration**: ~5-7 minutes  
**Total tests**: 500  
**Use case**: Stress test under peak load

### 5. Extreme Stress Test
```bash
python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 20 --delay 0
```
**Duration**: ~10-15 minutes  
**Total tests**: 2000  
**Use case**: Maximum load testing, finding breaking points

## 📊 What to Expect

### Normal Mode
- **Speed**: ~20-30 tests/min
- **Load**: Low
- **Use**: Development, debugging

### Continuous Mode
- **Speed**: ~30-40 tests/min
- **Load**: Low-Medium
- **Use**: Endurance testing

### Aggressive Mode (5 threads)
- **Speed**: ~100-150 tests/min
- **Load**: Medium-High
- **Use**: Load testing

### Aggressive Mode (10 threads)
- **Speed**: ~200-300 tests/min
- **Load**: High
- **Use**: Stress testing

### Aggressive Mode (20 threads)
- **Speed**: ~400-600 tests/min
- **Load**: Extreme
- **Use**: Breaking point testing

## 🛑 How to Stop

- Press **Ctrl+C** to stop gracefully
- Results will be saved and printed
- Logs are preserved

## 📝 Output Files

- **Log file**: `parlay_autoplay_{timestamp}.log`
- **Market lines**: `fresh_market_lines.json`

## 💡 Pro Tips

1. **Start small**: Begin with normal mode to verify setup
2. **Fresh lines daily**: Run `python utils/fetch_market_lines.py` daily
3. **Monitor logs**: Check log files for detailed error info
4. **Gradual ramp**: Increase load gradually to find limits
5. **Ctrl+C friendly**: Always use Ctrl+C for clean shutdown

## ⚠️ Common Issues

### "No market lines available"
```bash
python utils/fetch_market_lines.py
```

### High failure rate
- Check if market lines are fresh (generated today)
- Verify SP credentials in `parlay_autoplay.py`
- Check API health/availability

### Slow performance
- Reduce `--concurrency`
- Increase `--delay`
- Check network connection

## 📚 More Information

See `LOAD_TESTING_README.md` for complete documentation.

---

**Happy Testing! 🎰**
