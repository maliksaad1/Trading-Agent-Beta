from solders.keypair import Keypair
import json
import os

def create_mainnet_wallet():
    # Create wallet directory if it doesn't exist
    os.makedirs('wallet', exist_ok=True)
    
    # Generate new keypair
    keypair = Keypair()
    
    # Save private key
    with open('./wallet/mainnet_wallet.json', 'w') as f:
        secret_bytes = list(keypair.secret())
        json.dump(secret_bytes, f)
        
    print("\n[WALLET CREATED]")
    print(f"Public Key: {keypair.pubkey()}")
    print("\nIMPORTANT: Save this public key to fund your wallet!")
    print("WARNING: Keep your wallet file secure and never share it!")

if __name__ == "__main__":
    create_mainnet_wallet() 