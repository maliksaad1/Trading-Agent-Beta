import asyncio
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.phantom_wallet import PhantomWallet
from agents.scout_agent import ScoutAgent
from utils.logger import setup_logger

async def test_monitor():
    logger = setup_logger("test_monitor")
    logger.info("Starting token monitoring test...")
    
    # Initialize wallet
    wallet = PhantomWallet()
    wallet_address = "CaLnEKFzDNzLCzJy4NaXfhcbFruzyEZV4VQmFUZ8Dfqk"  # Your Phantom address
    
    await wallet.initialize(wallet_address)
    balance = await wallet.check_balance()
    logger.info(f"Wallet Balance: {balance:.4f} SOL")
    
    # Initialize scout agent
    scout = ScoutAgent()
    
    # Add callback to print token info
    async def token_callback(token_data):
        logger.info(
            f"\n[NEW TOKEN DETECTED]"
            f"\n  Symbol: {token_data['symbol']}"
            f"\n  Price: ${token_data['initial_price']:.8f}"
            f"\n  Liquidity: ${token_data['liquidity']:,.2f}"
            f"\n  Source: {token_data['source']}"
            f"\n  Address: {token_data['address']}"
        )
    
    # Subscribe to token notifications
    await scout.subscribe(token_callback)
    
    logger.info("Starting token monitoring...")
    logger.info("Press Ctrl+C to stop")
    
    # Start monitoring
    await scout.start()

def main():
    print("Starting Solana token monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(test_monitor())
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 