import asyncio
from agents.scout_agent import ScoutAgent
from agents.trading_agent import TradingAgent
from agents.analysis_agent import AnalysisAgent
from utils.wallet_manager import WalletManager
from utils.logger import setup_logger
from datetime import datetime

def setup_bot_logger():
    return setup_logger("trading_bot")

class TradingBot:
    def __init__(self):
        # Initialize logger first
        self.logger = setup_bot_logger()
        self.is_running = False
        self.active_trades = []
        self.scout_agent = None
        self.trading_agent = None
        self.wallet_manager = None
        self._tasks = []
        self.logger.info("TradingBot initialized")

    async def initialize_components(self):
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing components...")

            # Initialize wallet manager
            self.wallet_manager = WalletManager()
            if not await self.wallet_manager.initialize():
                raise Exception("Failed to initialize wallet manager")
            self.logger.info("Wallet manager initialized")

            # Initialize trading agent
            self.trading_agent = TradingAgent(self.wallet_manager)
            if not await self.trading_agent.initialize():
                raise Exception("Failed to initialize trading agent")
            self.logger.info("Trading agent initialized")

            # Initialize scout agent
            self.scout_agent = ScoutAgent()
            if not await self.scout_agent.initialize():
                raise Exception("Failed to initialize scout agent")
            self.logger.info("Scout agent initialized")

            # Subscribe trading agent to scout agent
            await self.scout_agent.subscribe(self.trading_agent.handle_new_token)
            self.logger.info("Trading agent subscribed to scout agent")

            self.logger.info("All components initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            # Cleanup any partially initialized components
            await self.cleanup_components()
            return False

    async def cleanup_components(self):
        """Cleanup all components"""
        try:
            if self.scout_agent:
                await self.scout_agent.cleanup()
            if self.trading_agent:
                await self.trading_agent.cleanup()
            if self.wallet_manager:
                await self.wallet_manager.cleanup()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    async def _start(self):
        """Start the bot"""
        try:
            if self.is_running:
                self.logger.warning("Bot is already running")
                return

            self.logger.info("Starting bot...")
            if await self.initialize_components():
                self.is_running = True
                
                # Start scout agent
                if self.scout_agent:
                    await self.scout_agent.start()
                    self.logger.info("Scout agent started")
                
                # Start trade monitoring
                if self.trading_agent:
                    monitor_task = asyncio.create_task(
                        self.trading_agent.monitor_active_trades()
                    )
                    self._tasks.append(monitor_task)
                    self.logger.info("Trade monitoring started")
                
                self.logger.info("Bot started successfully")
            else:
                raise Exception("Failed to initialize components")

        except Exception as e:
            self.logger.error(f"Failed to start bot: {str(e)}")
            await self.cleanup_components()
            raise

    async def _stop(self):
        """Stop the bot"""
        if not self.is_running:
            self.logger.warning("Bot is not running")
            return

        try:
            self.logger.info("Stopping bot...")
            self.is_running = False
            
            # Cancel all running tasks
            for task in self._tasks:
                task.cancel()
            self._tasks.clear()
            
            # Cleanup components
            await self.cleanup_components()
            self.logger.info("Bot stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping bot: {str(e)}")
            raise

    def get_status(self):
        """Get bot status"""
        return "Online" if self.is_running else "Offline"

    def get_monitored_tokens(self):
        """Get monitored tokens from scout agent"""
        try:
            if self.scout_agent and self.is_running:
                return self.scout_agent.get_cached_tokens()
            return []
        except Exception as e:
            self.logger.error(f"Error getting monitored tokens: {str(e)}")
            return []

    def get_active_trades(self):
        """Get active trades from trading agent"""
        try:
            if self.trading_agent and self.is_running:
                return self.trading_agent.active_trades
            return {}
        except Exception as e:
            self.logger.error(f"Error getting active trades: {str(e)}")
            return {} 