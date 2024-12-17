import asyncio
import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from main import TradingBot
from utils.trading_verifier import TradingVerifier
from utils.wallet_manager import WalletManager
from utils.dexscreener import DexScreener
from utils.logger import setup_logger

async def verify_complete_system():
    logger = setup_logger("system_verifier")
    logger.info("\n=== COMPLETE SYSTEM VERIFICATION ===")
    
    try:
        # 1. Check Components
        logger.info("\n1. Checking Core Components...")
        bot = TradingBot()
        verifier = TradingVerifier()
        
        # 2. Verify Network
        logger.info("\n2. Testing Network Connectivity...")
        dex = DexScreener()
        await dex.initialize()
        test_pair = await dex.search_pairs("SOL/USDC")
        if test_pair and 'pairs' in test_pair:
            logger.info("✅ DexScreener API working")
        await dex.close()
        
        # 3. Verify Agents
        logger.info("\n3. Testing Agent Chain...")
        # Scout -> Trading -> Analysis -> Exit
        test_token = {
            'symbol': 'TEST',
            'address': 'So11111111111111111111111111111111111111112',
            'initial_price': 0.001,
            'supply': 50000,
            'liquidity': 1000,
            'volume_24h': 100,
            'created_at': time.time(),
            'dex': 'raydium'
        }
        
        # Test agent chain
        await bot.scout_agent.initialize()
        await bot.trading_agent.initialize()
        await bot.analysis_agent.initialize()
        await bot.exit_agent.initialize()
        logger.info("✅ All agents initialized")
        
        # 4. Verify Trading Parameters
        logger.info("\n4. Verifying Trading Parameters...")
        params = bot.trading_agent.token_requirements
        logger.info(
            f"Trading Parameters:\n"
            f"  Min Liquidity: ${params['min_liquidity']}\n"
            f"  Min Volume 24h: ${params['min_volume_24h']}\n"
            f"  Max Token Age: {params['max_age_seconds']}s\n"
            f"  Required DEX: {params['required_dexes']}"
        )
        
        # 5. Run Complete Verification
        logger.info("\n5. Running Complete System Check...")
        if await verifier.verify_all_components(bot):
            logger.info("\n✅ SYSTEM VERIFICATION COMPLETE - ALL CHECKS PASSED")
            logger.info(
                "\nSystem Status:"
                "\n- Network: Connected"
                "\n- Agents: Initialized"
                "\n- Parameters: Configured"
                "\n- Monitoring: Ready"
            )
            if bot.wallet_manager.phantom_public_key:
                logger.info(f"- Wallet: Connected ({bot.wallet_manager.phantom_public_key})")
            else:
                logger.info("- Wallet: Monitor Only Mode")
                
            logger.info("\nSystem is ready for:")
            logger.info("1. Token Detection")
            logger.info("2. Market Analysis")
            logger.info("3. Price Monitoring")
            if bot.wallet_manager.phantom_public_key:
                logger.info("4. Trading Operations")
            
            return True
        else:
            logger.error("\n❌ System verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False
    finally:
        await bot.cleanup()

if __name__ == "__main__":
    asyncio.run(verify_complete_system()) 