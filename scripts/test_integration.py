import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TradingBot
from utils.logger import setup_logger
from utils.config import config

async def test_integration():
    logger = setup_logger("integration_test")
    logger.info("Starting integration test...")
    
    try:
        # 1. Create bot instance
        logger.info("\n1. Creating bot instance...")
        bot = TradingBot()
        
        # 2. Test wallet connection
        logger.info("\n2. Testing wallet connection...")
        wallet = bot.trading_agent.wallet_manager
        await wallet.initialize()
        balance = await wallet.check_balance()
        logger.info(f"Wallet Balance: {balance:.4f} SOL")
        
        # 3. Test scout agent
        logger.info("\n3. Testing scout agent...")
        scout = bot.scout_agent
        
        # Add test callback
        async def test_callback(token_data):
            logger.info(
                f"\nToken detected:"
                f"\n  Symbol: {token_data['symbol']}"
                f"\n  Price: ${token_data['initial_price']:.8f}"
                f"\n  Liquidity: ${token_data['liquidity']:,.2f}"
            )
            
        await scout.subscribe(test_callback)
        
        # 4. Test analysis agent
        logger.info("\n4. Testing analysis agent...")
        analysis = bot.analysis_agent
        await analysis.initialize()
        
        # 5. Test trading agent
        logger.info("\n5. Testing trading agent...")
        trader = bot.trading_agent
        await trader.initialize()
        
        # 6. Test exit agent
        logger.info("\n6. Testing exit agent...")
        exit_agent = bot.exit_agent
        
        # 7. Test full communication chain
        logger.info("\n7. Testing communication chain...")
        
        # Create test token data
        test_token = {
            'address': 'So11111111111111111111111111111111111111112',
            'symbol': 'TEST',
            'initial_price': 1.0,
            'liquidity': 10000,
            'source': 'Test'
        }
        
        # Simulate token detection
        logger.info("Simulating new token detection...")
        await scout.notify_new_token(test_token)
        
        # Wait briefly for processing
        await asyncio.sleep(2)
        
        # Check if token was processed
        if test_token['address'] in trader.active_trades:
            logger.info("✓ Token successfully processed through chain")
        
        # 8. Test UI updates (if UI exists)
        if bot.ui:
            logger.info("\n8. Testing UI updates...")
            bot.ui.add_log_message("Integration test running")
            bot.ui.add_new_token(test_token)
            logger.info("✓ UI updates successful")
            
        logger.info("\nIntegration test completed successfully!")
        
    except Exception as e:
        logger.error(f"\nIntegration test failed: {str(e)}")
    finally:
        # Cleanup
        await bot.stop()

def main():
    print("Starting integration test...")
    asyncio.run(test_integration())

if __name__ == "__main__":
    main() 