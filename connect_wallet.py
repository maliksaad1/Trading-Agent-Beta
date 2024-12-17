import asyncio
from utils.wallet_connector import PhantomConnector
from utils.wallet_manager import WalletManager

async def connect_phantom():
    """Connect and verify Phantom wallet"""
    try:
        # Connect wallet
        connector = PhantomConnector()
        wallet_address = await connector.connect()
        
        # Verify connection
        wallet_manager = WalletManager()
        await wallet_manager.initialize()
        
        # Check balance
        balance = await wallet_manager.check_balance()
        print(f"\nWallet connected successfully!")
        print(f"Address: {wallet_address}")
        print(f"Balance: {balance:.4f} SOL")
        
        await wallet_manager.cleanup()
        
    except Exception as e:
        print(f"\nError connecting wallet: {str(e)}")

if __name__ == "__main__":
    asyncio.run(connect_phantom()) 