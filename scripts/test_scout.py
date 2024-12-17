import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scout_agent import ScoutAgent
from utils.logger import setup_logger

async def test_scout():
    logger = setup_logger("test_scout")
    scout = ScoutAgent()
    
    # Add test callback
    async def test_callback(token_data):
        logger.info(f"Detected: {token_data['symbol']} at ${token_data['initial_price']:.8f}")
    
    await scout.subscribe(test_callback)
    
    # Test DexScreener connection
    logger.info("Testing DexScreener connection...")
    async with scout.session:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        async with scout.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                pairs = data.get('pairs', [])
                logger.info(f"Found {len(pairs)} pairs on DexScreener")
            else:
                logger.error(f"DexScreener returned status {response.status}")
    
    # Start monitoring
    logger.info("Starting scout agent...")
    await scout.start()

if __name__ == "__main__":
    print("Testing scout agent...")
    asyncio.run(test_scout()) 