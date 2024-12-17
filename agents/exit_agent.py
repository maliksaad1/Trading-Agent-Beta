import asyncio
import aiohttp
import base64
from solana.transaction import Transaction
from utils.logger import setup_logger

class ExitAgent:
    def __init__(self, wallet_manager):
        self.logger = setup_logger("exit_agent")
        self.wallet_manager = wallet_manager
        self.is_initialized = False

    async def initialize(self):
        """Initialize exit agent"""
        try:
            self.is_initialized = True
            self.logger.info("Exit agent initialized")
            return True
        except Exception as e:
            self.logger.error(f"Exit agent initialization failed: {str(e)}")
            return False

    async def execute_sell(self, token_address, amount, reason="manual"):
        """Execute sell order using Jupiter Swap API"""
        session = None
        try:
            session = aiohttp.ClientSession()
            
            # 1. Get quote from Jupiter
            quote_url = f"https://quote-api.jup.ag/v6/quote"
            params = {
                'inputMint': token_address,
                'outputMint': 'So11111111111111111111111111111111111111112',  # SOL
                'amount': str(amount),
                'slippageBps': 50  # 0.5% slippage
            }
            
            async with session.get(quote_url, params=params) as response:
                quote_data = await response.json()

            # 2. Get swap transaction
            swap_url = "https://quote-api.jup.ag/v6/swap"
            swap_data = {
                'quoteResponse': quote_data,
                'userPublicKey': str(self.wallet_manager.phantom_public_key),
                'wrapUnwrapSOL': True
            }
            
            async with session.post(swap_url, json=swap_data) as response:
                transaction_data = await response.json()
                
            # 3. Deserialize and sign transaction
            tx_bytes = base64.b64decode(transaction_data['swapTransaction'])
            transaction = Transaction.deserialize(tx_bytes)
            
            # 4. Sign and send
            transaction.sign([self.wallet_manager.keypair])
            txid = await self.wallet_manager.client.send_transaction(
                transaction,
                opts={'skipPreflight': True}
            )

            if not await self._wait_for_confirmation(txid):
                raise Exception("Transaction failed to confirm")

            self.logger.info(f"Sell transaction sent: {txid} (Reason: {reason})")
            return True

        except Exception as e:
            self.logger.error(f"Sell order failed: {str(e)}")
            return False
        finally:
            if session:
                await session.close()

    async def _wait_for_confirmation(self, signature):
        """Wait for transaction confirmation"""
        try:
            await self.wallet_manager.client.confirm_transaction(
                signature,
                commitment="confirmed"
            )
            return True
        except Exception as e:
            self.logger.error(f"Transaction confirmation failed: {str(e)}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Nothing to clean up for now
            self.logger.info("Exit agent cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
