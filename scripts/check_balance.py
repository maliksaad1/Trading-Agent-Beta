import asyncio
from solana.rpc.async_api import AsyncClient
import json
from solders.keypair import Keypair

async def check_balance():
    try:
        # Load wallet
        with open('./wallet/mainnet_wallet.json', 'r') as f:
            private_key = json.load(f)
        keypair = Keypair.from_bytes(bytes(private_key))
        
        # Check balance
        client = AsyncClient("https://api.mainnet-beta.solana.com")
        balance = await client.get_balance(keypair.pubkey())
        print(f"\nWallet Balance: {balance.value/1e9:.4f} SOL")
        await client.close()
        
    except Exception as e:
        print(f"Error checking balance: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_balance()) 