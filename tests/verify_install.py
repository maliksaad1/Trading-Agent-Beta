import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

async def test_imports():
    print("Testing Solana package imports...")
    
    try:
        # Test client
        client = AsyncClient("https://api.devnet.solana.com")
        print("✓ AsyncClient import successful")
        
        # Test keypair
        kp = Keypair()
        print("✓ Keypair generation successful")
        print(f"  Generated public key: {kp.pubkey()}")
        
        # Test RPC connection
        version = await client.get_version()
        print(f"✓ RPC connection successful")
        print(f"  Solana version: {version.value.solana_core}")
        
        await client.close()
        print("\nAll imports working correctly!")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_imports()) 