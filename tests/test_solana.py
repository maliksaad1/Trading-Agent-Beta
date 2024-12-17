import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

async def test_solana():
    print("Testing Solana installation...")
    
    try:
        # Create client
        client = AsyncClient("https://api.devnet.solana.com")
        print("✓ Client created successfully")
        
        # Test connection
        response = await client.is_connected()
        print(f"✓ Connection test: {response}")
        
        # Create keypair
        kp = Keypair()
        print(f"✓ Keypair created: {kp.pubkey()}")
        
        await client.close()
        print("\nAll tests passed!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Try reinstalling the packages")
        print("2. Check Python version (3.7+ required)")
        print("3. Try installing from source")

if __name__ == "__main__":
    asyncio.run(test_solana()) 