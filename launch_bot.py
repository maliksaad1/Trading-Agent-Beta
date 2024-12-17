import streamlit as st
import asyncio
import concurrent.futures
from bot import TradingBot
import time
from ui import TradingBotUI
import platform

def setup_windows_event_loop():
    """Setup proper event loop for Windows"""
    if platform.system() == 'Windows':
        loop = asyncio.ProactorEventLoop()
        loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        asyncio.set_event_loop(loop)
        return loop
    return asyncio.get_event_loop()

# Configure Streamlit page
st.set_page_config(
    page_title="Solana Trading Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

if 'bot' not in st.session_state:
    st.session_state.bot = TradingBot()
    st.session_state.bot.logger.info("Bot instance created")

if 'is_running' not in st.session_state:
    st.session_state.is_running = False

if 'loop' not in st.session_state:
    try:
        loop = setup_windows_event_loop()
        st.session_state.loop = loop
        st.session_state.bot.logger.info("Event loop initialized")
    except Exception as e:
        st.error(f"Failed to initialize event loop: {str(e)}")

# Initialize UI with bot instance
if 'ui' not in st.session_state:
    st.session_state.ui = TradingBotUI(st.session_state.bot)
    st.session_state.bot.logger.info("UI initialized")

def start_bot():
    """Start the bot and handle errors"""
    if not st.session_state.is_running:
        try:
            with st.spinner("Starting bot..."):
                loop = st.session_state.loop
                loop.run_until_complete(st.session_state.bot._start())
                st.session_state.is_running = True
                st.success("Bot started successfully!")
                time.sleep(1)  # Give components time to initialize
        except Exception as e:
            st.error(f"Failed to start bot: {str(e)}")
            st.session_state.bot.logger.error(f"Start error: {str(e)}")

def stop_bot():
    """Stop the bot and handle errors"""
    if st.session_state.is_running:
        try:
            with st.spinner("Stopping bot..."):
                loop = st.session_state.loop
                loop.run_until_complete(st.session_state.bot._stop())
                st.session_state.is_running = False
                st.success("Bot stopped successfully!")
        except Exception as e:
            st.error(f"Failed to stop bot: {str(e)}")
            st.session_state.bot.logger.error(f"Stop error: {str(e)}")

# Add control buttons in sidebar
with st.sidebar:
    st.title("Bot Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button('▶️ Start', key='start_button', disabled=st.session_state.is_running):
            start_bot()
    with col2:
        if st.button('⏹️ Stop', key='stop_button', disabled=not st.session_state.is_running):
            stop_bot()
    
    # Show bot status
    status = "🟢 Online" if st.session_state.is_running else "🔴 Offline"
    st.info(f"Bot Status: {status}")

# Run the UI
try:
    st.session_state.ui.render()
except Exception as e:
    st.error(f"UI error: {str(e)}")
    st.session_state.bot.logger.error(f"UI error: {str(e)}")

# Cleanup on exit
def cleanup():
    if st.session_state.is_running:
        stop_bot()

# Register cleanup function
import atexit
atexit.register(cleanup) 