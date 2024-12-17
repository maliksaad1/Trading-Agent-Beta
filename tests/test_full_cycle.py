import asyncio
from main import TradingBot
import time

async def test_trading_cycle():
    print("\nStarting full cycle test...")
    bot = TradingBot()
    
    try:
        # Initialize bot
        print("\n1. Initializing bot...")
        await bot.setup()
        
        # Check wallet balance
        wallet = bot.trading_agent.wallet_manager
        balance = await wallet.check_balance()
        print(f"\nWallet Balance: {balance:.4f} SOL")
        
        # Test token detection
        print("\n2. Testing token detection...")
        test_token = {
            'address': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'symbol': 'wSOL',
            'initial_price': 1.0
        }
        
        # Simulate new token detection
        await bot.scout_agent.notify_new_token(test_token)
        
        # Wait for trade processing
        print("\n3. Waiting for trade processing...")
        await asyncio.sleep(5)
        
        # Check if trade was recorded
        if test_token['address'] in bot.trading_agent.active_trades:
            print("Trade successfully opened!")
            trade_info = bot.trading_agent.active_trades[test_token['address']]
            print(f"Position Size: {trade_info['position_size']:.4f} SOL")
            
            # Test position closing
            print("\n4. Testing position closing...")
            await bot.trading_agent.close_position({
                'token_address': test_token['address'],
                'current_price': 1.1,  # Simulated profit
                'reason': 'TEST_CLOSE'
            })
            
            if test_token['address'] not in bot.trading_agent.active_trades:
                print("Position successfully closed!")
        
        print("\nFinal wallet balance:", await wallet.check_balance())
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    finally:
        # Cleanup
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(test_trading_cycle()) 