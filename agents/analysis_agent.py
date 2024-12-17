import time
from utils.logger import setup_logger

class AnalysisAgent:
    def __init__(self, exit_agent=None):
        self.logger = setup_logger("analysis_agent")
        self.is_initialized = False
        self.exit_agent = exit_agent
        self.active_trades = {}
        
        # Analysis parameters
        self.params = {
            'take_profit_usdc': 0.05,  # $0.05 USDC take profit
            'stop_loss': -4.0,         # 4% stop loss
            'max_trades': 5            # Maximum concurrent trades
        }

    async def initialize(self):
        """Initialize analysis agent"""
        try:
            if not self.exit_agent:
                self.logger.error("No exit agent provided")
                return False
                
            self.is_initialized = True
            self.logger.info("Analysis agent initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize analysis agent: {str(e)}")
            return False

    async def process_price_update(self, price_data):
        """Process price updates and trigger exits at $0.05 USDC profit"""
        try:
            token_address = price_data['address']
            current_price = float(price_data['price'])
            
            if token_address in self.active_trades:
                trade = self.active_trades[token_address]
                entry_price = trade['entry_price']
                position_size = trade['position_size']
                
                # Calculate profit/loss in USDC
                price_diff = current_price - entry_price
                profit_usdc = price_diff * position_size
                pl_pct = (price_diff / entry_price) * 100
                
                # Log current status
                self.logger.info(
                    f"\n📊 Trade Status: {token_address}\n"
                    f"  Entry: ${entry_price:.8f}\n"
                    f"  Current: ${current_price:.8f}\n"
                    f"  P/L: ${profit_usdc:.3f} USDC ({pl_pct:.3f}%)"
                )
                
                # Check exit conditions
                if profit_usdc >= self.params['take_profit_usdc']:
                    self.logger.info(f"🎯 Take Profit triggered at ${profit_usdc:.3f} USDC")
                    await self._execute_exit(token_address, current_price, "take_profit")
                    
                elif pl_pct <= self.params['stop_loss']:
                    self.logger.info(f"🛑 Stop Loss triggered at {pl_pct:.3f}%")
                    await self._execute_exit(token_address, current_price, "stop_loss")
                    
        except Exception as e:
            self.logger.error(f"Error processing price update: {str(e)}")

    async def process_trade_update(self, trade_data):
        """Process new trade notifications"""
        try:
            # Check if we're at max trades
            if len(self.active_trades) >= self.params['max_trades']:
                self.logger.info("Maximum active trades reached, skipping new trade")
                return
            
            # Add new trade to monitoring
            self.active_trades[trade_data['token_address']] = {
                'entry_price': trade_data['entry_price'],
                'position_size': trade_data['position_size'],
                'entry_time': trade_data['entry_time']
            }
            
            self.logger.info(
                f"\n📈 Monitoring New Trade:\n"
                f"  Token: {trade_data['token_address']}\n"
                f"  Entry: ${trade_data['entry_price']:.8f}\n"
                f"  Size: {trade_data['position_size']} SOL\n"
                f"  Target: +$0.05 USDC\n"
                f"  Stop: -4.00%"
            )
            
        except Exception as e:
            self.logger.error(f"Error processing trade update: {str(e)}")

    async def _execute_exit(self, token_address, current_price, reason):
        """Execute exit through exit agent"""
        try:
            trade = self.active_trades[token_address]
            
            # Calculate final P/L
            price_diff = current_price - trade['entry_price']
            profit_usdc = price_diff * trade['position_size']
            pl_pct = (price_diff / trade['entry_price']) * 100
            
            # Execute sell through exit agent
            success = await self.exit_agent.execute_sell(
                token_address=token_address,
                amount=trade['position_size'],
                reason=reason
            )
            
            if success:
                self.logger.info(
                    f"\n🔄 Position Closed:\n"
                    f"  Token: {token_address}\n"
                    f"  Reason: {reason}\n"
                    f"  Entry: ${trade['entry_price']:.8f}\n"
                    f"  Exit: ${current_price:.8f}\n"
                    f"  P/L: ${profit_usdc:.3f} USDC ({pl_pct:.3f}%)"
                )
                # Remove from active trades
                del self.active_trades[token_address]
                
                # Log available slots
                self.logger.info(f"Active Trades: {len(self.active_trades)}/{self.params['max_trades']}")
                
        except Exception as e:
            self.logger.error(f"Error executing exit: {str(e)}")

    async def cleanup(self):
        """Cleanup resources"""
        self.active_trades.clear()
