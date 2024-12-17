import asyncio
from collections import deque
import time
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.commitment import Confirmed
from raydium.instructions import (
    create_swap_instruction,
    get_pool_info,
    calculate_min_out_amount
)
from utils.logger import setup_logger
from utils.config import config
from utils.wallet_manager import WalletManager
from solders.instruction import Instruction
from solders.system_program import create_account, CreateAccountParams
from utils.exceptions import (
    InsufficientBalanceError, 
    InvalidTokenError, 
    TransactionError,
    TokenAccountError
)
import aiohttp
from utils.dexscreener import DexScreener
import base64
from dotenv import load_dotenv
import os

load_dotenv()

class TradingAgent:
    def __init__(self, wallet_manager=None):
        self.logger = setup_logger("trading_agent")
        self.wallet_manager = wallet_manager
        self.active_trades = {}
        self.execution_times = deque(maxlen=100)
        self.is_initialized = False
        self.session = None
        
        # Trading parameters
        self.MAX_TOKEN_AGE = 120  # 2 minutes in seconds
        self.POSITION_SIZE = 0.1  # 0.1 SOL per trade
        self.MAX_TRADES = 5
        self.TAKE_PROFIT = 0.5  # 50%
        self.STOP_LOSS = -0.2   # -20%

    async def initialize(self):
        """Initialize trading agent"""
        try:
            # Verify wallet connection
            if not self.wallet_manager:
                self.logger.error("No wallet manager provided")
                return False
            
            if not self.wallet_manager.is_initialized:
                self.logger.error("Wallet manager not initialized")
                return False
            
            balance = await self.wallet_manager.check_balance()
            self.logger.info(
                f"Trading agent initialized:\n"
                f"  Wallet connected: {self.wallet_manager.phantom_public_key}\n"
                f"  Balance: {balance:.4f} SOL"
            )
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Trading agent initialization failed: {str(e)}")
            return False

    async def handle_new_token(self, token_data):
        """Handle new token from scout agent"""
        try:
            self.logger.info(f"\n🔄 Processing token: {token_data['symbol']}")
            
            # Skip if maximum trades reached
            if len(self.active_trades) >= self.MAX_TRADES:
                self.logger.info("Maximum active trades reached, skipping")
                return
            
            # Skip if token already traded
            if token_data['address'] in self.active_trades:
                self.logger.info("Token already in active trades, skipping")
                return
            
            # Check token age
            token_age = time.time() - token_data.get('created_at', 0)
            self.logger.info(f"Token age: {token_age:.1f} seconds")
            
            if token_age > self.MAX_TOKEN_AGE:
                self.logger.info(f"Token too old (>{self.MAX_TOKEN_AGE}s), skipping")
                return
            
            # Check wallet balance
            balance = await self.wallet_manager.check_balance()
            self.logger.info(f"Wallet balance: {balance:.4f} SOL")
            
            if balance < self.POSITION_SIZE:
                self.logger.info(f"Insufficient balance for {self.POSITION_SIZE} SOL trade")
                return
            
            self.logger.info(f"Attempting to buy {token_data['symbol']}...")
            success = await self._execute_buy_order(token_data, self.POSITION_SIZE)
            
            if success:
                self.active_trades[token_data['address']] = {
                    'token_data': token_data,
                    'entry_price': float(token_data['price']),
                    'position_size': self.POSITION_SIZE,
                    'entry_time': time.time()
                }
                
                self.logger.info(
                    f"\n✅ Trade Opened:\n"
                    f"  Token: {token_data['symbol']}\n"
                    f"  Entry: ${token_data['price']:.8f}\n"
                    f"  Size: {self.POSITION_SIZE} SOL\n"
                    f"  Age: {token_age:.1f} seconds\n"
                    f"  Active Trades: {len(self.active_trades)}/{self.MAX_TRADES}"
                )
            
        except Exception as e:
            self.logger.error(f"Error handling token {token_data.get('symbol')}: {str(e)}")

    async def monitor_active_trades(self):
        """Monitor active trades for take profit/stop loss"""
        while True:
            try:
                for address, trade in list(self.active_trades.items()):
                    # Get current price from Jupiter
                    price_url = f"https://price.jup.ag/v4/price?ids={address}"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(price_url) as response:
                            if response.status == 200:
                                price_data = await response.json()
                                if price_data['data'].get(address):
                                    current_price = float(price_data['data'][address]['price'])
                                    
                                    # Calculate profit/loss
                                    entry_price = trade['entry_price']
                                    price_change = (current_price - entry_price) / entry_price
                                    
                                    # Take profit at 50%
                                    if price_change >= self.TAKE_PROFIT:
                                        self.logger.info(f"Take profit triggered for {trade['token_data']['symbol']}")
                                        await self._execute_sell_order(address, trade, "TAKE_PROFIT")
                                    
                                    # Stop loss at -20%
                                    elif price_change <= self.STOP_LOSS:
                                        self.logger.info(f"Stop loss triggered for {trade['token_data']['symbol']}")
                                        await self._execute_sell_order(address, trade, "STOP_LOSS")
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Monitor error: {str(e)}")
                await asyncio.sleep(1)

    async def close_position(self, exit_signal):
        """Close position using Raydium API"""
        try:
            token_address = exit_signal['token_address']
            trade_info = self.active_trades.get(token_address)
            if not trade_info:
                self.logger.error(f"No active trade found for token {token_address}")
                return False
            
            # Calculate optimal slippage for this sell
            slippage = await self._calculate_optimal_slippage(
                trade_info['token_data'],
                trade_info['position_size'],
                is_buy=False
            )
            
            async with aiohttp.ClientSession() as session:
                # Get quote for selling
                quote_response = await self._execute_with_retry(
                    session.get,
                    f"{config.RAYDIUM_API_URL}/compute/swap-base-out",
                    params={
                        'inputMint': token_address,
                        'outputMint': 'So11111111111111111111111111111111111111112',
                        'amount': str(trade_info['position_size']),
                        'slippageBps': int(slippage * 100),  # Dynamic slippage
                        'txVersion': 'V0'
                    }
                )
                quote_data = await quote_response.json()

                # 2. Get transaction from Raydium API
                priority_fee = await self._get_priority_fee()
                swap_response = await self._execute_with_retry(
                    session.post,
                    f"{config.RAYDIUM_API_URL}/transaction/swap-base-out",
                    json={
                        'computeUnitPriceMicroLamports': priority_fee,
                        'swapResponse': quote_data,
                        'txVersion': 'V0',
                        'wallet': str(self.wallet_manager.phantom_public_key),
                        'wrapSol': True,
                        'unwrapSol': False
                    }
                )
                swap_data = await swap_response.json()

                # 3. Deserialize and execute transaction
                tx_bytes = base64.b64decode(swap_data['data'][0]['transaction'])
                transaction = Transaction.deserialize(tx_bytes)
                
                # 4. Sign and send
                transaction.sign([self.wallet_manager.keypair])
                txid = await self.wallet_manager.client.send_transaction(
                    transaction,
                    opts={'skipPreflight': True}
                )

                if not await self._wait_for_confirmation(txid):
                    raise TransactionError("Transaction failed to confirm")

                self.logger.info(f"Sell transaction sent: {txid}")
                if txid:  # If transaction successful
                    self.logger.info(
                        f"\n[POSITION CLOSED]"
                        f"\n  Token: {trade_info['token_data']['symbol']}"
                        f"\n  Entry: ${trade_info['entry_price']:.8f}"
                        f"\n  Exit: ${exit_signal['current_price']:.8f}"
                        f"\n  P/L: {exit_signal['profit_percentage']:.2f}%"
                        f"\n  Reason: {exit_signal['reason']}"
                    )
                    del self.active_trades[token_address]  # Remove the closed position
                    return True

        except Exception as e:
            self.logger.error(f"Sell order failed: {str(e)}")
            return False

    async def set_analysis_callback(self, price_callback, trade_callback):
        """Set analysis callbacks with validation"""
        if not callable(price_callback) or not callable(trade_callback):
            raise ValueError("Callbacks must be callable functions")
            
        self.analysis_callbacks = [
            {'type': 'price', 'func': price_callback},
            {'type': 'trade', 'func': trade_callback}
        ]
        
    async def validate_market_cap(self, token_data):
        """
        Validate if token's market cap is between $100-$25,000
        Returns: (bool, float) - (is_valid, market_cap)
        """
        try:
            # Get supply and price
            supply = float(token_data.get('supply', 0))
            current_price = float(token_data.get('initial_price', 0))
            
            # Calculate market cap in USD
            market_cap = supply * current_price
            
            # Validate market cap is between 100 and 25000 USD
            is_valid = self.MIN_MARKET_CAP <= market_cap <= self.MAX_MARKET_CAP
            
            if not is_valid:
                if market_cap < self.MIN_MARKET_CAP:
                    self.logger.info(
                        f"Token {token_data['symbol']} skipped: "
                        f"Market cap ${market_cap:.2f} below minimum (${self.MIN_MARKET_CAP})"
                    )
                else:
                    self.logger.info(
                        f"Token {token_data['symbol']} skipped: "
                        f"Market cap ${market_cap:.2f} exceeds ${self.MAX_MARKET_CAP}"
                    )
            else:
                self.logger.info(
                    f"Token {token_data['symbol']} validated: "
                    f"Market cap ${market_cap:.2f} - Within target range (${self.MIN_MARKET_CAP}-${self.MAX_MARKET_CAP})"
                )
                
            return is_valid, market_cap
            
        except Exception as e:
            self.logger.error(f"Error calculating market cap: {str(e)}")
            return False, 0

    async def _execute_with_retry(self, func, *args, max_retries=3, **kwargs):
        """Execute function with retry logic and timing"""
        start_time = time.perf_counter()
        
        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                self.execution_times.append(time.perf_counter() - start_time)
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(f"Retry attempt {attempt + 1}: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def _notify_analysis(self, trade_info):
        """Notify analysis agent in parallel"""
        for callback in self.analysis_callbacks:
            asyncio.create_task(callback['func'](trade_info))

    async def _get_token_account(self, token_address):
        """Get token account for a specific token"""
        try:
            # Get token accounts owned by wallet using Pubkey
            response = await self.wallet_manager.client.get_token_accounts_by_owner(
                self.wallet_manager.keypair.public_key(),
                {'mint': Pubkey.from_string(token_address)},
                commitment=Confirmed
            )
            
            accounts = response['result']['value']
            if accounts:
                return accounts[0]['pubkey']
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token account: {str(e)}")
            return None
            
    async def _create_token_account(self, token_address):
        """Create a new token account"""
        try:
            # Create minimum rent exempt balance instruction
            rent = await self.wallet_manager.client.get_minimum_balance_for_rent_exemption(
                165  # Token account size
            )
            
            # Create new account
            new_account = Keypair()
            
            # Create token account instruction
            create_account_ix = create_account(
                CreateAccountParams(
                    from_pubkey=self.wallet_manager.phantom_public_key,
                    new_account_pubkey=new_account.public_key(),
                    lamports=rent['result'],
                    space=165,
                    program_id=TOKEN_PROGRAM_ID
                )
            )
            
            # Create and send transaction
            transaction = Transaction()
            transaction.add(create_account_ix)
            
            result = await self.wallet_manager.sign_and_send_transaction(
                transaction,
                {"skipPreflight": True}
            )
            
            if not result:
                raise TokenAccountError("Failed to create token account")
                
            return new_account.public_key()
            
        except Exception as e:
            self.logger.error(f"Error creating token account: {str(e)}")
            raise TokenAccountError(f"Token account creation failed: {str(e)}")

    async def _get_or_create_token_account(self, token_address):
        """Get existing token account or create new one"""
        account = await self._get_token_account(token_address)
        if account:
            return account
            
        return await self._create_token_account(token_address)

    async def _calculate_optimal_slippage(self, token_data, trade_amount, is_buy=True):
        """Calculate optimal slippage based on market conditions"""
        try:
            # Get pool liquidity
            liquidity = float(token_data.get('liquidity', 0))
            
            # Calculate trade impact (trade size relative to liquidity)
            trade_impact = (trade_amount / liquidity) * 100 if liquidity > 0 else 100
            
            # Base slippage starts at 0.5%
            base_slippage = 0.5
            
            # Adjust for trade impact
            if trade_impact > 1:  # If trade is >1% of liquidity
                base_slippage += (trade_impact * 0.5)  # Add 0.5% per 1% of liquidity
            
            # Adjust for volatility (if available)
            if 'price_change_24h' in token_data:
                volatility = abs(float(token_data['price_change_24h']))
                base_slippage += (volatility * 0.1)  # Add 0.1% per 1% volatility
            
            # Add extra buffer for buys vs sells
            if is_buy:
                base_slippage += 0.5  # Extra 0.5% for buys
            
            # Cap maximum slippage
            max_slippage = 5.0 if is_buy else 3.0
            final_slippage = min(base_slippage, max_slippage)
            
            self.logger.info(
                f"Calculated slippage: {final_slippage:.2f}%\n"
                f"  Trade impact: {trade_impact:.2f}%\n"
                f"  Liquidity: ${liquidity:,.2f}"
            )
            
            return final_slippage
            
        except Exception as e:
            self.logger.error(f"Error calculating slippage: {str(e)}")
            return 1.0  # Default to 1% if calculation fails

    async def _execute_buy_order(self, token_data, amount_sol):
        """Execute buy order using Jupiter Swap API"""
        try:
            # Create session for Jupiter API
            async with aiohttp.ClientSession() as session:
                # 1. Get quote from Jupiter
                quote_url = "https://quote-api.jup.ag/v6/quote"
                params = {
                    'inputMint': 'So11111111111111111111111111111111111111112',  # SOL
                    'outputMint': token_data['address'],
                    'amount': str(int(amount_sol * 1e9)),  # Convert SOL to lamports
                    'slippageBps': '1000',  # 10% slippage for new tokens
                    'onlyDirectRoutes': 'true',
                    'asLegacyTransaction': 'true'
                }
                
                self.logger.info(f"Getting Jupiter quote for {token_data['symbol']}...")
                async with session.get(quote_url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Jupiter quote error: {await response.text()}")
                    quote_data = await response.json()

                # 2. Get swap transaction
                swap_url = "https://quote-api.jup.ag/v6/swap"
                swap_data = {
                    'quoteResponse': quote_data,
                    'userPublicKey': str(self.wallet_manager.phantom_public_key),
                    'wrapUnwrapSOL': True,
                    'computeUnitPriceMicroLamports': 50000,  # Higher priority
                    'asLegacyTransaction': True
                }
                
                self.logger.info("Getting swap transaction...")
                async with session.post(swap_url, json=swap_data) as response:
                    if response.status != 200:
                        raise Exception(f"Jupiter swap error: {await response.text()}")
                    transaction_data = await response.json()

                # 3. Sign and send transaction
                tx_bytes = base64.b64decode(transaction_data['swapTransaction'])
                transaction = Transaction.deserialize(tx_bytes)
                transaction.sign(self.wallet_manager.keypair)
                
                # 4. Send with retries
                for attempt in range(3):
                    try:
                        txid = await self.wallet_manager.client.send_transaction(
                            transaction,
                            opts={'skipPreflight': True}
                        )
                        
                        self.logger.info(f"Transaction sent: {txid}")
                        
                        # Wait for confirmation
                        await self.wallet_manager.client.confirm_transaction(
                            txid,
                            commitment="confirmed"
                        )
                        
                        self.logger.info("Transaction confirmed!")
                        return True
                        
                    except Exception as e:
                        if attempt == 2:  # Last attempt
                            raise
                        self.logger.warning(f"Retry {attempt + 1}/3: {str(e)}")
                        await asyncio.sleep(1)
                
                return False

        except Exception as e:
            self.logger.error(f"Buy order failed: {str(e)}")
            return False

    async def _get_priority_fee(self):
        """Get recommended priority fee from Raydium"""
        try:
            async with aiohttp.ClientSession() as session:
                response = await self._execute_with_retry(
                    session.get,
                    f"{config.RAYDIUM_API_URL}/priority-fee"
                )
                data = await response.json()
                return str(data['data']['default']['high'])
        except Exception as e:
            self.logger.error(f"Error getting priority fee: {str(e)}")
            return "1000"  # Default fallback fee

    def get_execution_time(self):
        return sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close session if exists
            if self.session:
                await self.session.close()
                self.session = None
                
            # Clear trades and state
            self.active_trades.clear()
            self.execution_times.clear()
            self.is_initialized = False
            
            self.logger.info("Trading agent cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    async def get_market_cap(self, token_address):
        """Get real-time market cap from multiple sources"""
        try:
            market_caps = []
            
            # 1. Try DexScreener
            dex_data = await self.dexscreener.get_token_pairs(token_address)
            if dex_data and 'pairs' in dex_data:
                for pair in dex_data['pairs']:
                    if 'fdv' in pair:  # Fully Diluted Valuation
                        market_caps.append(float(pair['fdv']))
            
            # 2. Calculate from supply and price
            pair_info = await self.get_dexscreener_pair(token_address)
            if pair_info:
                supply = float(pair_info['baseToken'].get('supply', 0))
                price = float(pair_info.get('priceUsd', 0))
                calculated_mcap = supply * price
                market_caps.append(calculated_mcap)
            
            # Return median if we have multiple values, otherwise the single value
            if market_caps:
                return sorted(market_caps)[len(market_caps)//2]
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting market cap: {str(e)}")
            return 0

    async def validate_token(self, token_data):
        """Validate token - only check age and basic requirements"""
        try:
            # 1. Check age first (most important)
            token_age = time.time() - token_data.get('created_at', 0)
            self.logger.info(f"Token Age: {token_age:.1f} seconds")
            if token_age > self.token_requirements['max_age_seconds']:
                self.logger.info(
                    f"Token {token_data['symbol']} skipped: "
                    f"Too old ({token_age:.1f} seconds > 60 seconds)"
                )
                return False, 0
            
            # 2. Check liquidity
            liquidity = token_data.get('liquidity', 0)
            if liquidity < self.token_requirements['min_liquidity']:
                self.logger.info(
                    f"Token {token_data['symbol']} skipped: "
                    f"Insufficient liquidity ${liquidity:.2f}"
                )
                return False, 0
            
            # 3. Check volume
            volume = token_data.get('volume_24h', 0)
            if volume < self.token_requirements['min_volume_24h']:
                self.logger.info(
                    f"Token {token_data['symbol']} skipped: "
                    f"Low 24h volume ${volume:.2f}"
                )
                return False, 0
            
            # 4. Check DEX
            dex = token_data.get('dex', '')
            if dex not in self.token_requirements['required_dexes']:
                self.logger.info(
                    f"Token {token_data['symbol']} skipped: "
                    f"Not on required DEX (found: {dex})"
                )
                return False, 0
            
            # Token passed all checks
            self.logger.info(
                f"\n✅ Token {token_data['symbol']} validated!\n"
                f"  Age: {token_age:.1f} seconds\n"
                f"  Liquidity: ${liquidity:.2f}\n"
                f"  24h Volume: ${volume:.2f}\n"
                f"  DEX: {dex}"
            )
            return True, 0  # Market cap no longer matters
            
        except Exception as e:
            self.logger.error(f"Error validating token: {str(e)}")
            return False, 0

    async def _wait_for_confirmation(self, signature):
        """Wait for transaction confirmation"""
        try:
            await self.wallet_manager.client.confirm_transaction(
                signature,
                commitment="confirmed"
            )
            return True
        except Exception as e:
            self.logger.error(f"Transaction confirmation failed: {str(e)}")
            return False

    async def _submit_transaction(self, transaction, retries=3):
        """Submit transaction with retries"""
        for attempt in range(retries):
            try:
                txid = await self.wallet_manager.client.send_transaction(
                    transaction,
                    opts={'skipPreflight': True}
                )
                if await self._wait_for_confirmation(txid):
                    return txid
            except Exception as e:
                if attempt == retries - 1:
                    raise
                self.logger.warning(f"Retry {attempt + 1}/{retries}: {str(e)}")
                await asyncio.sleep(1)
        return None

    async def monitor_new_tokens(self):
        """Monitor for new token launches"""
        while True:
            try:
                # Get new tokens from DexScreener
                new_tokens = await self.dexscreener.get_new_tokens()
                
                for token in new_tokens:
                    self.logger.info(f"\nNew token detected: {token['symbol']}")
                    
                    # Validate token
                    is_valid, _ = await self.validate_token(token)
                    if not is_valid:
                        continue
                    
                    # Check wallet balance
                    balance = await self.wallet_manager.check_balance()
                    if balance < config.POSITION_SIZE_SOL:
                        self.logger.info(f"Insufficient balance: {balance:.4f} SOL")
                        continue
                    
                    # Execute buy
                    await self._execute_buy_order(token, config.POSITION_SIZE_SOL)
                    
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Error monitoring new tokens: {str(e)}")
                await asyncio.sleep(1)
