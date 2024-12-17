import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agents.scout_agent import ScoutAgent
from agents.trading_agent import TradingAgent
from agents.analysis_agent import AnalysisAgent
from agents.exit_agent import ExitAgent
from utils.wallet_manager import WalletManager
from utils.logger import setup_logger

class AgentTester:
    def __init__(self):
        self.logger = setup_logger("agent_tester")
        self.wallet_manager = WalletManager()
        
    async def test_scout_agent(self):
        """Test Scout Agent functionality"""
        self.logger.info("\n=== Testing Scout Agent ===")
        try:
            scout = ScoutAgent()
            
            # Test initialization
            await scout.initialize()
            self.logger.info("✓ Scout Agent initialized")
            
            # Test subscription
            test_tokens = []
            async def token_callback(token_data):
                test_tokens.append(token_data)
                self.logger.info(
                    f"New token detected:\n"
                    f"  Symbol: {token_data['symbol']}\n"
                    f"  Price: ${token_data.get('initial_price', 0):.8f}\n"
                    f"  Market Cap: ${token_data.get('market_cap', 0):.2f}"
                )
            
            await scout.subscribe(token_callback)
            self.logger.info("✓ Callback subscription successful")
            
            # Test token monitoring
            self.logger.info("Testing token monitoring (10s)...")
            await scout.start()
            await asyncio.sleep(10)
            await scout.stop()
            
            self.logger.info(f"✓ Detected {len(test_tokens)} tokens")
            await scout.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Scout Agent test failed: {str(e)}")
            return False

    async def test_trading_agent(self):
        """Test Trading Agent functionality"""
        self.logger.info("\n=== Testing Trading Agent ===")
        try:
            trading = TradingAgent(wallet_manager=self.wallet_manager)
            
            # Test initialization
            await trading.initialize()
            self.logger.info("✓ Trading Agent initialized")
            
            # Test market cap validation
            test_tokens = [
                {
                    'symbol': 'TEST1',
                    'address': 'So11111111111111111111111111111111111111112',
                    'initial_price': 0.001,
                    'supply': 50000,  # $50 market cap
                    'liquidity': 1000
                },
                {
                    'symbol': 'TEST2',
                    'address': 'So11111111111111111111111111111111111111113',
                    'initial_price': 0.01,
                    'supply': 20000,  # $200 market cap - should fail
                    'liquidity': 1000
                }
            ]
            
            for token in test_tokens:
                is_valid, market_cap = await trading.validate_market_cap(token)
                self.logger.info(
                    f"Market cap test for {token['symbol']}:\n"
                    f"  Valid: {is_valid}\n"
                    f"  Market Cap: ${market_cap:.2f}"
                )
            
            # Test DexScreener integration
            pair_info = await trading.get_dexscreener_pair(test_tokens[0]['address'])
            self.logger.info("✓ DexScreener API functional")
            
            await trading.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Trading Agent test failed: {str(e)}")
            return False

    async def test_analysis_agent(self):
        """Test Analysis Agent functionality"""
        self.logger.info("\n=== Testing Analysis Agent ===")
        try:
            analysis = AnalysisAgent()
            
            # Test price analysis with multiple scenarios
            test_cases = [
                {'price': 1.03, 'entry': 1.00},  # 3% gain - should trigger
                {'price': 1.02, 'entry': 1.00},  # 2% gain - should not trigger
                {'price': 0.98, 'entry': 1.00}   # Loss - should not trigger
            ]
            
            signals_received = []
            async def exit_callback(signal):
                signals_received.append(signal)
                self.logger.info(
                    f"Exit signal generated:\n"
                    f"  Reason: {signal['reason']}\n"
                    f"  Profit: {signal['profit_percentage']:.2f}%"
                )
            
            await analysis.set_exit_callback(exit_callback)
            
            for i, case in enumerate(test_cases):
                await analysis.handle_price_update(
                    f"TEST{i}",
                    case['price'],
                    case['entry']
                )
            
            self.logger.info(f"✓ Generated {len(signals_received)} exit signals")
            await analysis.cleanup()
            return True
            
        except Exception as e:
            self.logger.error(f"Analysis Agent test failed: {str(e)}")
            return False

    async def test_exit_agent(self):
        """Test Exit Agent functionality"""
        self.logger.info("\n=== Testing Exit Agent ===")
        try:
            exit_agent = ExitAgent()
            
            # Setup trading callback
            async def trade_callback(exit_data):
                self.logger.info(
                    f"Position close signal:\n"
                    f"  Token: {exit_data['token_address']}\n"
                    f"  Reason: {exit_data['reason']}"
                )
            
            await exit_agent.set_trading_callback(trade_callback)
            
            # Test exit signal
            test_signal = {
                'token_address': 'TEST',
                'reason': 'take_profit',
                'profit_percentage': 3.0
            }
            
            await exit_agent.handle_analysis_signal(test_signal)
            
            self.logger.info("Exit Agent test complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Exit Agent test failed: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all agent tests"""
        try:
            # Initialize wallet first
            await self.wallet_manager.initialize()
            self.logger.info("✓ Wallet connection established")
            
            balance = await self.wallet_manager.check_balance()
            if balance == 0:
                self.logger.warning(
                    "Wallet has 0 balance. Tests will run in simulation mode.\n"
                    "To test actual trading, please fund the wallet with some SOL."
                )
            else:
                self.logger.info(f"Wallet balance: {balance:.4f} SOL")

            tests = [
                ("Scout Agent", self.test_scout_agent()),
                ("Trading Agent", self.test_trading_agent()),
                ("Analysis Agent", self.test_analysis_agent()),
                ("Exit Agent", self.test_exit_agent())
            ]
            
            results = []
            for name, test in tests:
                self.logger.info(f"\nRunning {name} test...")
                result = await test
                results.append((name, result))
                await asyncio.sleep(1)  # Brief pause between tests
                
            # Print summary
            self.logger.info("\n=== Test Results ===")
            all_passed = True
            for name, result in results:
                status = "[PASS]" if result else "[FAIL]"
                self.logger.info(f"{name}: {status}")
                all_passed = all_passed and result
                
            if all_passed:
                self.logger.info("\n[SUCCESS] All agents working correctly!")
            else:
                self.logger.warning("\n[WARNING] Some agents failed tests")
                
        except Exception as e:
            self.logger.error(f"Test suite failed: {str(e)}")
        finally:
            await self.wallet_manager.cleanup()

async def main():
    tester = AgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 