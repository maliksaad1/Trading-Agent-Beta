import asyncio
from utils.wallet_manager import WalletManager
from utils.logger import setup_logger

async def initialize_connections():
    logger = setup_logger("initializer")
    wallet = None
    
    try:
        logger.info("\n=== Initializing Connections ===")
        
        # Initialize wallet manager
        wallet = WalletManager()
        await wallet.initialize()
        
        # Check RPC connection
        if wallet.client:
            is_connected = await wallet.client.is_connected()
            logger.info(
                f"RPC Connection: {'✅ Connected' if is_connected else '❌ Failed'}\n"
                f"Endpoint: {wallet.client.endpoint}"
            )
        
        # Check wallet
        if wallet.phantom_public_key:
            balance = await wallet.check_balance()
            logger.info(
                f"\nWallet Status:\n"
                f"  Address: {wallet.phantom_public_key}\n"
                f"  Balance: {balance:.4f} SOL"
            )
        
        logger.info("\n✅ Connection initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        return False
    finally:
        if wallet:
            await wallet.cleanup()

if __name__ == "__main__":
    asyncio.run(initialize_connections()) 