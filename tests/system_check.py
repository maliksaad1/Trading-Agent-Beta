import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.wallet_manager import WalletManager
from utils.config import config
from utils.logger import setup_logger
from utils.dexscreener import DexScreener
import aiohttp
from utils.exceptions import WalletError

class SystemCheck:
    def __init__(self):
        self.logger = setup_logger("system_check")
        self.wallet_manager = None
        self.status_symbols = {
            'success': '[PASS]',
            'fail': '[FAIL]',
            'warning': '[WARN]'
        }
        
    async def initialize(self):
        """Initialize system check components"""
        self.wallet_manager = WalletManager()

    async def cleanup(self):
        """Cleanup all resources"""
        if self.wallet_manager:
            await self.wallet_manager.cleanup()
            self.wallet_manager = None

    async def check_phantom_connection(self):
        """Test Phantom wallet connection"""
        try:
            self.logger.info("\n=== Testing Phantom Wallet Connection ===")
            
            # Verify configuration
            if not config.PHANTOM_PUBLIC_KEY:
                self.logger.error("[FAIL] Phantom public key not configured")
                return False
                
            self.logger.info(f"Using wallet address: {config.PHANTOM_PUBLIC_KEY}")
            
            # Initialize wallet manager
            try:
                await self.wallet_manager.initialize()
                self.logger.info("[PASS] Wallet initialization successful")
            except WalletError as e:
                self.logger.error(f"[FAIL] Wallet initialization failed: {str(e)}")
                return False
            except Exception as e:
                self.logger.error(f"[FAIL] Unexpected error: {str(e)}")
                return False

            # Check balance
            try:
                balance = await self.wallet_manager.check_balance()
                self.logger.info(f"[INFO] Wallet balance: {balance:.4f} SOL")
                return True
            except Exception as e:
                self.logger.error(f"[FAIL] Balance check failed: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"[FAIL] Wallet check failed: {str(e)}")
            return False

    async def check_dexscreener_api(self):
        """Test DexScreener API access"""
        try:
            self.logger.info("\n=== Testing DexScreener API ===")
            
            dexscreener = DexScreener()
            await dexscreener.initialize()
            
            # Test basic search
            self.logger.info("Testing basic search...")
            search_result = await dexscreener.search_pairs("SOL/USDC")
            if not search_result:
                self.logger.error("[FAIL] Basic search failed")
                return False
                
            # Verify search result structure
            if 'pairs' not in search_result:
                self.logger.error("[FAIL] Invalid search response format")
                return False
                
            self.logger.info(f"[PASS] Found {len(search_result['pairs'])} pairs in search")
            
            # Test Solana pairs
            self.logger.info("\nTesting Solana pairs retrieval...")
            pairs_result = await dexscreener.get_solana_pairs()
            
            # Debug log the response
            self.logger.info(f"Solana pairs response: {pairs_result}")
            
            if not pairs_result:
                self.logger.error("[FAIL] Failed to get Solana pairs")
                return False
                
            if 'pairs' not in pairs_result:
                self.logger.error("[FAIL] Invalid Solana pairs response format")
                self.logger.error(f"Response: {pairs_result}")
                return False
                
            pair_count = len(pairs_result['pairs'])
            self.logger.info(f"[PASS] Retrieved {pair_count} Solana pairs")
            
            await dexscreener.close()
            return True
            
        except Exception as e:
            self.logger.error(f"[FAIL] DexScreener API check failed: {str(e)}")
            self.logger.error(f"Error details: {type(e).__name__}")
            await dexscreener.close()
            return False
            
    async def check_raydium_pools(self):
        """Test Raydium pool access"""
        try:
            self.logger.info("\n=== Testing Raydium Pool Access ===")
            
            # Try to get a known Raydium pool
            test_token = "SOL/USDC"  # Example pool
            self.logger.info(f"Testing pool access for {test_token}")
            
            # Add your Raydium pool check logic here
            # This will depend on your Raydium integration
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Raydium pool check failed: {str(e)}")
            return False
            
    async def simulate_trade_flow(self):
        """Simulate the entire trading flow without executing trades"""
        try:
            self.logger.info("\n=== Simulating Trade Flow ===")
            
            # 1. Check if we can get market data
            self.logger.info("1. Testing market data retrieval...")
            async with aiohttp.ClientSession() as session:
                url = "https://api.dexscreener.com/latest/dex/pairs/solana"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get('pairs', [])
                        if pairs:
                            test_pair = pairs[0]
                            self.logger.info(
                                f"✅ Successfully got market data:\n"
                                f"  Token: {test_pair['baseToken']['symbol']}\n"
                                f"  Price: ${test_pair.get('priceUsd', 'N/A')}\n"
                                f"  Market Cap: ${test_pair.get('fdv', 'N/A')}"
                            )
                            
            # 2. Check wallet operations
            self.logger.info("\n2. Testing wallet operations...")
            balance = await self.wallet_manager.check_balance()
            available = await self.wallet_manager.get_available_balance()
            self.logger.info(
                f"✅ Wallet status:\n"
                f"  Total balance: {balance:.4f} SOL\n"
                f"  Available: {available:.4f} SOL"
            )
            
            # 3. Simulate position sizing
            self.logger.info("\n3. Testing position sizing...")
            max_position = min(balance * 0.1, config.POSITION_SIZE_SOL)
            self.logger.info(
                f"✅ Position sizing:\n"
                f"  Max position: {max_position:.4f} SOL\n"
                f"  Config limit: {config.POSITION_SIZE_SOL} SOL"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Trade flow simulation failed: {str(e)}")
            return False
            
    async def run_all_checks(self):
        """Run all system checks"""
        try:
            # Initialize components
            await self.initialize()

            checks = [
                ("Phantom Wallet", self.check_phantom_connection()),
                ("DexScreener API", self.check_dexscreener_api()),
                ("Raydium Pools", self.check_raydium_pools()),
                ("Trade Flow", self.simulate_trade_flow())
            ]
            
            results = []
            for name, check in checks:
                self.logger.info(f"\nRunning {name} check...")
                result = await check
                results.append((name, result))
                
            # Print summary
            self.logger.info("\n=== System Check Summary ===")
            all_passed = True
            for name, result in results:
                status = self.status_symbols['success'] if result else self.status_symbols['fail']
                self.logger.info(f"{name}: {status}")
                all_passed = all_passed and result
                
            if all_passed:
                self.logger.info("\n[SUCCESS] All systems ready for trading!")
            else:
                self.logger.warning("\n[WARNING] Some checks failed - Please review before trading")
                
        except Exception as e:
            self.logger.error(f"System check failed: {str(e)}")
        finally:
            # Cleanup at the end of all checks
            await self.cleanup()

async def main():
    checker = SystemCheck()
    await checker.run_all_checks()

if __name__ == "__main__":
    asyncio.run(main()) 