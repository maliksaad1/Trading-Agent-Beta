from agents.scout_agent import ScoutAgent
import time
import signal
import sys

def main():
    # Create scout agent
    scout = ScoutAgent()
    
    def signal_handler(sig, frame):
        print("\nShutdown signal received. Cleaning up...")
        cleanup(scout)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("🔄 Initializing scout agent...")
        if scout.initialize():
            print("🚀 Starting token monitoring...")
            scout.start()
            
            # Keep running and display new tokens
            while True:
                token = scout.get_new_tokens(timeout=1)
                if token:
                    print(f"\n💎 New token found: {token['symbol']}")
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n⚠️ Bot interrupted by user. Cleaning up...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        cleanup(scout)

def cleanup(scout):
    """Clean up resources"""
    try:
        scout.cleanup()
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    print("Starting Token Monitor...")
    main()
