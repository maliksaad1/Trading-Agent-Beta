import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from main import TradingBot
from utils.trading_verifier import TradingVerifier

async def main():
    bot = TradingBot()
    verifier = TradingVerifier()
    
    if await verifier.verify_all_components(bot):
        print("\n✅ System ready for live trading!")
    else:
        print("\n❌ System not ready. Please fix issues before live trading.")

if __name__ == "__main__":
    asyncio.run(main()) 