import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
import json
import time

async def get_devnet_sol():
    try:
        # Load existing wallet
        print("Loading wallet...")
        with open('./wallet/test_wallet.json', 'r') as f:
            private_key = json.load(f)
        keypair = Keypair.from_bytes(bytes(private_key))
        
        print(f"Wallet public key: {keypair.pubkey()}")
        
        # Connect to multiple devnet endpoints
        endpoints = [
            "https://api.devnet.solana.com",
            "https://devnet.solana.rpcpool.com",
            "https://api.testnet.solana.com"
        ]
        
        for endpoint in endpoints:
            print(f"\nTrying endpoint: {endpoint}")
            client = AsyncClient(endpoint)
            
            try:
                # Check initial balance
                initial_balance = await client.get_balance(keypair.pubkey())
                print(f"Initial balance: {initial_balance.value/1e9:.4f} SOL")
                
                # Request small airdrops multiple times
                for i in range(3):
                    print(f"\nAirdrop attempt {i+1}/3...")
                    
                    try:
                        # Request 0.5 SOL
                        result = await client.request_airdrop(
                            keypair.pubkey(),
                            500_000_000  # 0.5 SOL
                        )
                        
                        if hasattr(result, 'value'):
                            print(f"Airdrop requested. Signature: {result.value}")
                            
                            # Wait for confirmation
                            print("Waiting for confirmation...")
                            await asyncio.sleep(10)
                            
                            # Verify balance increased
                            new_balance = await client.get_balance(keypair.pubkey())
                            print(f"Current balance: {new_balance.value/1e9:.4f} SOL")
                            
                            if new_balance.value > initial_balance.value:
                                print("\nAirdrop successful!")
                                await client.close()
                                return True
                    except Exception as e:
                        print(f"Airdrop attempt failed: {str(e)}")
                        await asyncio.sleep(1)
                        continue
                        
            except Exception as e:
                print(f"Error with endpoint {endpoint}: {str(e)}")
            finally:
                await client.close()
                
        print("\nAll airdrop attempts failed")
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Requesting devnet SOL...")
    success = asyncio.run(get_devnet_sol())
    
    if success:
        print("\nSuccessfully got devnet SOL! You can now run the bot.")
    else:
        print("\nFailed to get devnet SOL. Please try:")
        print("1. Wait a few minutes and try again")
        print("2. Try at a different time")
        print("3. Check if devnet is operational") 