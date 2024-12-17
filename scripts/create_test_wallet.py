from solders.keypair import Keypair
import json
import os
from solana.rpc.async_api import AsyncClient
import asyncio
from pathlib import Path

async def request_airdrop(client, pubkey, amount):
    """Request airdrop with better error handling"""
    try:
        result = await client.request_airdrop(pubkey, amount)
        if hasattr(result, 'value'):
            return result.value
        return None
    except Exception as e:
        print(f"Airdrop request failed: {str(e)}")
        return None

async def create_test_wallet():
    # Create wallet directory if it doesn't exist
    wallet_dir = Path(__file__).parent.parent / 'wallet'
    wallet_dir.mkdir(exist_ok=True)
    
    # Generate new keypair
    keypair = Keypair()
    
    # Save private key
    wallet_path = wallet_dir / 'test_wallet.json'
    with open(wallet_path, 'w') as f:
        secret_bytes = list(keypair.secret())
        json.dump(secret_bytes, f)
        
    print(f"Public Key: {keypair.pubkey()}")
    print(f"Wallet saved to: {wallet_path.absolute()}")
    
    # Try different RPC endpoints
    endpoints = [
        "https://api.devnet.solana.com",
        "https://devnet.solana.rpcpool.com",
        "https://devnet.genesysgo.net"
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        client = AsyncClient(endpoint)
        
        try:
            # Request multiple smaller airdrops
            for i in range(5):  # Try 5 times
                print(f"\nAirdrop attempt {i+1}/5...")
                
                # Request 0.1 SOL each time
                signature = await request_airdrop(
                    client,
                    keypair.pubkey(),
                    100_000_000  # 0.1 SOL in lamports
                )
                
                if signature:
                    print(f"Airdrop requested. Signature: {signature}")
                    
                    # Wait for confirmation
                    print("Waiting for confirmation...")
                    await asyncio.sleep(5)
                    
                    # Check balance
                    balance = await client.get_balance(keypair.pubkey())
                    current_balance = balance.value / 1e9
                    print(f"Current balance: {current_balance:.4f} SOL")
                    
                    if current_balance > 0:
                        print("\nAirdrop successful!")
                        await client.close()
                        return True
                        
                await asyncio.sleep(1)  # Wait between attempts
                
        except Exception as e:
            print(f"Error with endpoint {endpoint}: {str(e)}")
        finally:
            await client.close()
            
    print("\nFailed to get airdrop from any endpoint")
    return False

def main():
    print("Creating test wallet...")
    success = asyncio.run(create_test_wallet())
    
    if success:
        print("\nWallet setup complete! You can now run the bot.")
    else:
        print("\nWallet created but airdrop failed. You may need to:")
        print("1. Try again later")
        print("2. Use Solana CLI to airdrop: solana airdrop 1 <your-public-key> --url devnet")
        print("3. Fund the wallet manually")

if __name__ == "__main__":
    main() 