import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TradingBot
from ui import TradingBotUI
from utils.logger import setup_logger
from utils.config import config

async def verify_live_setup():
    logger = setup_logger("live_verify")
    logger.info("Starting live mode verification...")
    
    try:
        # 1. Create bot instance
        logger.info("\n1. Creating bot instance...")
        bot = TradingBot()
        
        # 2. Create UI
        logger.info("\n2. Creating UI...")
        ui = TradingBotUI(bot)
        bot.ui = ui  # Connect UI to bot
        
        # 3. Verify wallet connection
        logger.info("\n3. Verifying wallet connection...")
        wallet = bot.trading_agent.wallet_manager
        await wallet.initialize()
        balance = await wallet.check_balance()
        logger.info(
            f"\n[WALLET STATUS]"
            f"\n  Address: {config.WALLET_ADDRESS}"
            f"\n  Balance: {balance:.4f} SOL"
            f"\n  Mode: {config.WALLET_MODE}"
        )
        
        # 4. Test Scout Agent
        logger.info("\n4. Testing Scout Agent...")
        scout = bot.scout_agent
        await scout.initialize()
        
        # Add test callback to verify token detection
        async def token_callback(token_data):
            logger.info(
                f"\n[NEW TOKEN DETECTED]"
                f"\n  Symbol: {token_data['symbol']}"
                f"\n  Price: ${token_data['initial_price']:.8f}"
                f"\n  Source: {token_data['source']}"
            )
            # Verify UI update
            ui.add_new_token(token_data)
            
        await scout.subscribe(token_callback)
        
        # 5. Test Analysis Agent
        logger.info("\n5. Testing Analysis Agent...")
        analysis = bot.analysis_agent
        await analysis.initialize()
        
        # 6. Test Trading Agent
        logger.info("\n6. Testing Trading Agent...")
        trader = bot.trading_agent
        await trader.initialize()
        
        # 7. Test Exit Agent
        logger.info("\n7. Testing Exit Agent...")
        exit_agent = bot.exit_agent
        
        # 8. Start monitoring
        logger.info("\n8. Starting monitoring...")
        logger.info("Press Ctrl+C to stop")
        
        # Start the bot
        await bot.start()
        
        # Start UI update loop
        ui.run()
        
    except KeyboardInterrupt:
        logger.info("\nStopping verification...")
    except Exception as e:
        logger.error(f"\nVerification failed: {str(e)}")
    finally:
        if 'bot' in locals():
            await bot.stop()

def main():
    print("\nStarting live mode verification...")
    print("This will:")
    print("1. Connect to your Phantom wallet")
    print("2. Start the UI")
    print("3. Monitor for new tokens")
    print("4. Show real-time updates")
    print("\nPress Ctrl+C to stop")
    
    try:
        asyncio.run(verify_live_setup())
    except KeyboardInterrupt:
        print("\nVerification stopped by user")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main() 