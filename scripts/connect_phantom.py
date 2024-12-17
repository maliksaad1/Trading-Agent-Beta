import asyncio
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.phantom_wallet import PhantomWallet
from utils.logger import setup_logger

async def connect_phantom():
    logger = setup_logger("phantom_connection")
    wallet = PhantomWallet()
    
    # Your Phantom wallet address from config
    wallet_address = "CaLnEKFzDNzLCzJy4NaXfhcbFruzyEZV4VQmFUZ8Dfqk"  # Your address
    
    success = await wallet.initialize(wallet_address)
    if success:
        logger.info("Successfully connected to Phantom wallet!")
        balance = await wallet.check_balance()
        logger.info(f"Wallet balance: {balance:.4f} SOL")
    else:
        logger.error("Failed to connect to Phantom wallet")

def main():
    print("Connecting to Phantom wallet...")
    asyncio.run(connect_phantom())

if __name__ == "__main__":
    main() 