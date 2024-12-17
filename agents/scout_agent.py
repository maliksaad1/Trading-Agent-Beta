import time
from utils.logger import setup_logger
from datetime import datetime
import requests
import threading
from queue import Queue

class ScoutAgent:
    def __init__(self):
        self.logger = setup_logger("scout_agent")
        self.is_running = False
        self.is_initialized = False
        self.known_tokens = set()
        self.token_cache = []
        self.last_token_count = 0
        self.token_queue = Queue()
        self.monitor_thread = None

    def initialize(self):
        """Initialize scout agent"""
        try:
            # Test connections
            self.logger.info("🔌 Testing API connections...")
            
            # Test Jupiter
            response = requests.get('https://token.jup.ag/all', timeout=10)
            if response.status_code != 200:
                raise Exception("❌ Failed to connect to Jupiter API")
                
            # Test DexScreener
            response = requests.get('https://api.dexscreener.com/latest/dex/tokens/solana', timeout=10)
            if response.status_code != 200:
                raise Exception("❌ Failed to connect to DexScreener API")
            
            self.is_initialized = True
            self.logger.info("✅ Scout agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Scout agent initialization failed: {str(e)}")
            return False

    def _monitor_tokens(self):
        """Monitor for new tokens"""
        while self.is_running:
            try:
                # Get tokens from Jupiter
                response = requests.get('https://token.jup.ag/all', timeout=10)
                if response.status_code == 200:
                    tokens = response.json()
                    current_count = len(tokens)
                    
                    if current_count != self.last_token_count:
                        self.logger.info(f"📊 Found {current_count} tokens on Jupiter")
                        self.last_token_count = current_count
                    
                    for token in tokens:
                        if token['address'] not in self.known_tokens:
                            self._process_new_token(token, '🪐 Jupiter')

                # Get tokens from DexScreener
                response = requests.get('https://api.dexscreener.com/latest/dex/tokens/solana', timeout=10)
                if response.status_code == 200:
                    dex_data = response.json()
                    if 'pairs' in dex_data:
                        for pair in dex_data['pairs']:
                            token = {
                                'address': pair['baseToken']['address'],
                                'symbol': pair['baseToken']['symbol'],
                                'name': pair['baseToken'].get('name', 'Unknown'),
                                'price': float(pair.get('priceUsd', 0)),
                                'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                                'volume': float(pair.get('volume', {}).get('h24', 0))
                            }
                            
                            if token['address'] not in self.known_tokens:
                                self._process_new_token(token, '🔍 DexScreener')

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.logger.error(f"⚠️ Monitor error: {str(e)}")
                time.sleep(1)

    def _process_new_token(self, token, source):
        """Process a new token"""
        try:
            self.logger.info(
                f"\n🔥 New Token Found on {source}!\n"
                f"  💎 Symbol: {token.get('symbol', 'Unknown')}\n"
                f"  📝 Name: {token.get('name', 'Unknown')}\n"
                f"  🔑 Address: {token['address']}\n"
                f"  💰 Price: ${token.get('price', 0):.8f}\n"
                f"  💧 Liquidity: ${token.get('liquidity', 0):,.2f}\n"
                f"  📈 Volume 24h: ${token.get('volume', 0):,.2f}"
            )

            token_info = {
                'address': token['address'],
                'symbol': token.get('symbol', 'Unknown'),
                'name': token.get('name', 'Unknown'),
                'price': token.get('price', 0),
                'liquidity': token.get('liquidity', 0),
                'volume': token.get('volume', 0),
                'created_at': int(time.time()),
                'source': source
            }

            self.token_cache.append(token_info)
            if len(self.token_cache) > 100:
                self.token_cache = self.token_cache[-100:]

            self.known_tokens.add(token['address'])
            self.token_queue.put(token_info)

        except Exception as e:
            self.logger.error(f"⚠️ Error processing token: {str(e)}")

    def start(self):
        """Start monitoring"""
        if not self.is_initialized:
            self.logger.error("❌ Cannot start - not initialized")
            return False

        self.is_running = True
        self.logger.info("🚀 Started monitoring for new tokens...")
        
        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=self._monitor_tokens)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return True

    def get_cached_tokens(self):
        """Get the cached token list"""
        return self.token_cache

    def get_new_tokens(self, timeout=0):
        """Get new tokens from the queue"""
        try:
            return self.token_queue.get(timeout=timeout)
        except:
            return None

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.logger.info("🧹 Cleaning up scout agent...")
            self.is_running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            
            self.known_tokens.clear()
            self.token_cache.clear()
            self.is_initialized = False
            
            self.logger.info("✨ Scout agent cleaned up")
            
        except Exception as e:
            self.logger.error(f"⚠️ Cleanup error: {str(e)}")
