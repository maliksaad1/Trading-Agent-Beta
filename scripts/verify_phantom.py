import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.phantom_wallet import PhantomWallet
from utils.logger import setup_logger
from utils.config import config

async def verify_phantom():
    logger = setup_logger("phantom_verify")
    wallet = PhantomWallet()
    
    try:
        logger.info("Connecting to Phantom wallet...")
        success = await wallet.initialize(config.WALLET_ADDRESS)
        
        if success:
            balance = await wallet.check_balance()
            logger.info(
                f"\n[WALLET VERIFIED]"
                f"\n  Address: {wallet.pubkey}"
                f"\n  Balance: {balance:.4f} SOL"
                f"\n  Network: Mainnet"
            )
            return True
        else:
            logger.error("Failed to connect to wallet")
            return False
            
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nVerifying Phantom wallet connection...")
    success = asyncio.run(verify_phantom())
    
    if success:
        print("\nWallet verification successful! You can now run the bot.")
    else:
        print("\nWallet verification failed. Please check:")
        print("1. Your wallet address in config.yaml")
        print("2. Your internet connection")
        print("3. Solana network status") 