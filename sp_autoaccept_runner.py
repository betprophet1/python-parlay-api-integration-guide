#!/usr/bin/env python3
"""
SP Auto-Acceptor for E2E Testing

Starts a WebSocket listener that automatically accepts all parlay offers.
Prints 'SP_READY' to stdout when connected and listening.
Used by Playwright E2E tests to provide parlay pricing.
"""
import sys
import os
import time
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from parlay_connect import ParlayInteractions

# Suppress verbose logging to avoid polluting test output
logging.basicConfig(level=logging.WARNING)

def main():
    pi = ParlayInteractions()

    print("[SP] Logging in...", flush=True)
    pi.login()

    print("[SP] Subscribing to WebSocket channels...", flush=True)
    pi.subscribe()

    # Wait for WebSocket connection to establish
    time.sleep(5)

    # Signal readiness to the parent process (Playwright test)
    print("SP_READY", flush=True)

    # Keep running until killed
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if pi.pusher:
            pi.pusher.disconnect()
        print("[SP] Auto-acceptor stopped", flush=True)

if __name__ == "__main__":
    main()
