import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
import json

async def request_devnet_sol():
    try:
        # Load existing wallet
        with open('./wallet/test_wallet.json', 'r') as f:
            private_key = json.load(f)
        keypair = Keypair.from_bytes(bytes(private_key))
        
        print(f"Requesting airdrop for: {keypair.pubkey()}")
        
        # Connect to devnet
        client = AsyncClient("https://api.devnet.solana.com")
        
        # Request airdrop
        print("\nRequesting 1 SOL...")
        result = await client.request_airdrop(
            keypair.pubkey(),
            1_000_000_000,  # 1 SOL in lamports
        )
        
        print(f"Airdrop requested: {result.value}")
        
        # Wait for confirmation
        print("\nWaiting for confirmation...")
        await asyncio.sleep(15)
        
        # Check balance
        balance = await client.get_balance(keypair.pubkey())
        print(f"\nCurrent balance: {balance.value/1e9:.4f} SOL")
        
        await client.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Requesting devnet SOL...")
    asyncio.run(request_devnet_sol()) 