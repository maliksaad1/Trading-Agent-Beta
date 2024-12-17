import aiohttp

class DexScreener:
    def __init__(self):
        self.session = None
        
    async def initialize(self):
        """Initialize the DexScreener service"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None 