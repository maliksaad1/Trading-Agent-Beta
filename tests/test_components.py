import asyncio
from utils.wallet_manager import WalletManager
from utils.rpc_manager import RPCManager
from agents.trading_agent import TradingAgent
import time

async def test_wallet():
    print("\nTesting Wallet Manager...")
    wallet = WalletManager()
    await wallet.initialize()
    balance = await wallet.check_balance()
    print(f"Wallet Balance: {balance} SOL")
    return wallet

async def test_rpc():
    print("\nTesting RPC Manager...")
    rpc = RPCManager()
    await rpc.initialize()
    endpoint = await rpc.get_best_endpoint()
    print(f"Best RPC Endpoint: {endpoint}")
    return rpc

async def test_trading_agent():
    print("\nTesting Trading Agent...")
    agent = TradingAgent()
    await agent.initialize()
    
    # Test token account creation
    test_token = {
        'address': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
        'symbol': 'wSOL',
        'initial_price': 1.0
    }
    
    account = await agent._get_or_create_token_account(test_token['address'])
    print(f"Token Account: {account}")
    return agent

async def main():
    try:
        wallet = await test_wallet()
        rpc = await test_rpc()
        agent = await test_trading_agent()
        
        print("\nAll components initialized successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    finally:
        # Cleanup
        if 'wallet' in locals():
            await wallet.client.close()
        if 'rpc' in locals():
            await rpc.close()

if __name__ == "__main__":
    asyncio.run(main()) 