import streamlit as st
from datetime import datetime
import time

class TradingBotUI:
    def __init__(self, bot):
        self.bot = bot
        # Initialize session state variables
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        if 'position_size' not in st.session_state:
            st.session_state.position_size = 0.1
        if 'take_profit' not in st.session_state:
            st.session_state.take_profit = 3
        if 'stop_loss' not in st.session_state:
            st.session_state.stop_loss = 2
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'last_token_count' not in st.session_state:
            st.session_state.last_token_count = 0

    def render(self):
        st.title("Token Monitoring")
        
        # Display bot status
        status = "Online" if self.bot.is_running else "Offline"
        status_color = "green" if self.bot.is_running else "red"
        st.markdown(f"<h2 style='color: {status_color}'>Bot {status}</h2>", unsafe_allow_html=True)
        
        # Display trading parameters in a sidebar
        with st.sidebar:
            st.subheader("Trading Parameters")
            position_size = st.number_input(
                "Position Size (SOL)", 
                min_value=0.1,
                max_value=1.0,
                value=st.session_state.position_size,
                step=0.1,
                key="position_size_input"
            )
            take_profit = st.number_input(
                "Take Profit %",
                min_value=1,
                max_value=10,
                value=st.session_state.take_profit,
                step=1,
                key="take_profit_input"
            )
            stop_loss = st.number_input(
                "Stop Loss %",
                min_value=1,
                max_value=10,
                value=st.session_state.stop_loss,
                step=1,
                key="stop_loss_input"
            )
            
            # Auto-refresh toggle
            st.session_state.auto_refresh = st.checkbox(
                "Auto Refresh",
                value=st.session_state.auto_refresh,
                key="auto_refresh_toggle"
            )
        
        # Create two columns for tokens and trades
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display monitored tokens
            st.subheader("Monitored Tokens")
            token_container = st.empty()
            
            if self.bot.is_running:
                monitored_tokens = self.bot.get_monitored_tokens()
                current_count = len(monitored_tokens)
                
                if monitored_tokens:
                    # Create a more compact display using a table
                    token_data = []
                    for token in monitored_tokens[-10:]:  # Show last 10 tokens
                        token_data.append({
                            "Symbol": token.get('symbol', 'Unknown'),
                            "Price": f"${token.get('price', 0):,.8f}",
                            "Age": f"{time.time() - token.get('created_at', time.time()):.1f}s"
                        })
                    
                    token_container.dataframe(
                        token_data,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Show token count and update if changed
                    if current_count != st.session_state.last_token_count:
                        st.metric(
                            "Total Tokens Found",
                            current_count,
                            delta=current_count - st.session_state.last_token_count
                        )
                        st.session_state.last_token_count = current_count
                else:
                    token_container.info("Waiting for tokens...")
            else:
                token_container.write("Bot is offline")
        
        with col2:
            # Display active trades
            st.subheader("Active Trades")
            trades_container = st.empty()
            
            if self.bot.is_running:
                active_trades = self.bot.get_active_trades()
                if active_trades:
                    trades_data = []
                    for address, trade in active_trades.items():
                        trades_data.append({
                            "Symbol": trade['token_data']['symbol'],
                            "Entry": f"${trade['entry_price']:.8f}",
                            "Size": f"{trade['position_size']} SOL"
                        })
                    trades_container.dataframe(
                        trades_data,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    trades_container.info("No active trades")
            else:
                trades_container.write("Bot is offline")
        
        # Manual refresh button
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🔄 Refresh", key="manual_refresh"):
                st.rerun()
        
        # Auto-refresh logic with rate limiting
        if self.bot.is_running and st.session_state.auto_refresh:
            current_time = datetime.now()
            if (current_time - st.session_state.last_update).total_seconds() > 2:
                st.session_state.last_update = current_time
                time.sleep(0.1)  # Small delay to prevent CPU overload
                st.rerun()  # Using st.rerun() instead of experimental_rerun