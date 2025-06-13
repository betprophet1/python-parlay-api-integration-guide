import parlay_connect
from log import logging
import time


def print_startup_banner():
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🎰 PARLAY API INTEGRATION                          ║
║                            Real-Time Betting System                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🚀 System Status: Starting Up                                               ║
║  📡 Mode: Live Trading                                                       ║
║  🎯 Target: Sports Betting Markets                                           ║
║  ⚡ Engine: Python Parlay Integration                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logging.info("🎰 PARLAY API INTEGRATION SYSTEM STARTING...")


if __name__ == '__main__':
    print_startup_banner()
    
    try:
        logging.info("\n🔧 Initializing Parlay Interactions...")
        mm_instance = parlay_connect.ParlayInteractions()
        
        logging.info("\n🔑 Step 1: Authenticating with API...")
        mm_instance.login()
        
        logging.info("\n💰 Step 2: Fetching account balance...")
        mm_instance.get_balance()
        
        logging.info("\n🌱 Step 3: Seeding tournaments and markets...")
        mm_instance.seeding()
        
        logging.info("\n📡 Step 4: Establishing WebSocket connections...")
        mm_instance.subscribe()
        
        logging.info("\n📋 Step 5: Sending supported betting lines...")
        mm_instance.send_supported_lines()
        
        # Final startup message
        logging.info("\n" + "="*80)
        logging.info("🎉 SYSTEM READY - LIVE TRADING ACTIVE!")
        logging.info("🔴 Listening for price quote requests...")
        logging.info("💚 Health monitoring enabled...")
        logging.info("⚡ Real-time processing active...")
        logging.info("="*80)
        
        logging.info("\n⏰ Starting keep-alive scheduler...")
        mm_instance.keep_alive()
        
    except KeyboardInterrupt:
        logging.info("\n\n🛑 SHUTDOWN SIGNAL RECEIVED")
        logging.info("👋 Gracefully shutting down Parlay API Integration...")
        logging.info("✅ System stopped successfully")
    except Exception as e:
        logging.error(f"\n❌ CRITICAL ERROR: {str(e)}")
        logging.error("🚨 System startup failed!")
        raise
