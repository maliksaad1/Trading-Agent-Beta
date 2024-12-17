import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TradingBot
from utils.logger import setup_logger
from utils.config import config

async def verify_live_setup():
    logger = setup_logger("live_setup")
    logger.info("Starting live setup verification...")
    
    try:
        # 1. Create bot instance
        logger.info("\n1. Creating bot instance...")
        bot = TradingBot()
        
        # 2. Verify Phantom wallet
        logger.info("\n2. Verifying Phantom wallet...")
        wallet = bot.trading_agent.wallet_manager
        await wallet.initialize()
        balance = await wallet.check_balance()
        logger.info(
            f"\n[WALLET STATUS]"
            f"\n  Address: {config.WALLET_ADDRESS}"
            f"\n  Balance: {balance:.4f} SOL"
            f"\n  Network: {'Mainnet' if 'mainnet' in config.RPC_ENDPOINTS[0] else 'Devnet'}"
        )
        
        # 3. Test Scout Agent Connection
        logger.info("\n3. Testing Scout Agent...")
        scout = bot.scout_agent
        await scout.initialize()
        
        # Add test callback to see new tokens
        async def token_callback(token_data):
            logger.info(
                f"\n[NEW TOKEN DETECTED]"
                f"\n  Symbol: {token_data['symbol']}"
                f"\n  Price: ${token_data['initial_price']:.8f}"
                f"\n  Liquidity: ${token_data['liquidity']:,.2f}"
                f"\n  Source: {token_data['source']}"
            )
            
        await scout.subscribe(token_callback)
        logger.info("Scout agent ready to monitor tokens")
        
        # 4. Start monitoring
        logger.info("\n4. Starting token monitoring...")
        logger.info("Monitoring for new tokens (press Ctrl+C to stop)...")
        
        # Start the scout agent
        await scout.start()
        
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user")
    except Exception as e:
        logger.error(f"\nSetup verification failed: {str(e)}")
    finally:
        # Cleanup
        if 'bot' in locals():
            await bot.stop()

def main():
    print("\nVerifying live setup with Phantom wallet...")
    print("This will check your wallet connection and start monitoring tokens")
    print("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(verify_live_setup())
    except KeyboardInterrupt:
        print("\nVerification stopped by user")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main() 