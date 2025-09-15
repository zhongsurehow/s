import asyncio
import random
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# --- Mock CCXT.PRO Implementation ---
# This block defines mock classes for ccxt.pro, allowing for development
# and testing without a licensed copy of the library.

class MockExchange:
    """Mocks a single ccxt.pro exchange connection."""
    def __init__(self, *args, **kwargs):
        """Accept any args to be robust, ignore them."""
        self._last_price = 50000 + random.uniform(-100, 100)

    async def watch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Simulates waiting for and receiving a single ticker update."""
        await asyncio.sleep(random.uniform(0.1, 0.5)) # Simulate network latency
        self._last_price *= random.uniform(0.999, 1.001)
        bid = self._last_price * 0.9998
        ask = self._last_price * 1.0002
        return {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'high': self._last_price * 1.02,
            'low': self._last_price * 0.98,
            'bid': bid,
            'ask': ask,
            'last': self._last_price,
            'baseVolume': random.uniform(1000, 5000),
            'info': {}, # Keep the structure consistent
        }

    async def watch_order_book(self, symbol: str, limit: int = 25) -> Dict[str, List]:
        """Simulates waiting for and receiving a single order book update."""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        price = 50000 + random.uniform(-100, 100)
        bids = sorted([[price - random.uniform(0, 10), random.uniform(0.1, 5)] for _ in range(limit)], key=lambda x: x[0], reverse=True)
        asks = sorted([[price + random.uniform(0, 10), random.uniform(0.1, 5)] for _ in range(limit)], key=lambda x: x[0])
        return {
            'bids': bids,
            'asks': asks,
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }

    async def close(self):
        """Simulates closing the connection."""
        logger.info("Mock exchange connection closed.")
        await asyncio.sleep(0.01)

    def fetch_deposit_withdraw_fees(self, codes=None, params={}):
        """Simulates fetching deposit and withdrawal fees."""
        logger.info("Mock exchange: fetching deposit/withdraw fees.")
        return {
            'USDT': {
                'info': {'coin': 'USDT'},
                'networks': {
                    'deposit': {
                        'TRX': {'fee': 0.0, 'percentage': False},
                        'ERC20': {'fee': 0.0, 'percentage': False},
                        'SOL': {'fee': 0.0, 'percentage': False},
                    },
                    'withdraw': {
                        'TRX': {'fee': 1.0, 'percentage': False},
                        'ERC20': {'fee': 25.0, 'percentage': False},
                        'SOL': {'fee': 0.5, 'percentage': False},
                    }
                }
            }
        }

class MockCCXTPro:
    """Mocks the ccxtpro library by dynamically creating MockExchange instances."""
    def __getattr__(self, name: str):
        # Return a constructor for a MockExchange
        return MockExchange

# --- Library Import ---
# This block attempts to import the real ccxt.pro library. If it fails,
# it logs a warning and prepares to use the mock implementation.
try:
    import ccxt.pro as ccxtpro
    IS_MOCK = False
except ImportError:
    logger.warning("ccxt.pro not found. Using a mock implementation for CEXProvider.")
    IS_MOCK = True
    ccxtpro = MockCCXTPro()

# --- Real CEX Provider ---
from .base import BaseProvider

class CEXProvider(BaseProvider):
    """
    Connects to Centralized Exchanges (CEX) using ccxt.pro (or a mock version)
    to get real-time data via WebSockets.
    """
    def __init__(self, name: str, config: Dict = None, force_mock: bool = False):
        super().__init__(name)
        self.exchange_id = name.lower()
        self.is_mock = force_mock or IS_MOCK  # Use mock if forced or if library is missing

        if self.is_mock:
            # When mocking, we know the class is MockExchange, so we instantiate it.
            self.exchange = MockExchange()
            return

        # --- The following code runs only if using the REAL ccxt.pro library ---
        try:
            exchange_class = getattr(ccxtpro, self.exchange_id)
            api_keys = config.get('api_keys', {}).get(self.exchange_id, {})
            # Use empty dict for public endpoints if no keys are provided
            self.exchange = exchange_class(api_keys if api_keys else {})
        except (AttributeError, TypeError) as e:
            # Re-raise with a more informative message
            raise ValueError(f"Exchange '{self.exchange_id}' is not supported by ccxt.pro or API config is invalid. Error: {e}")

    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches the next ticker data update from the WebSocket stream.
        The mock class has its own simulated latency, so no special handling is needed.
        """
        return await self.exchange.watch_ticker(symbol)

    async def get_order_book(self, symbol: str, limit: int = 25) -> Dict[str, List]:
        """
        Fetches the next order book data update from the WebSocket stream.
        The mock class has its own simulated latency, so no special handling is needed.
        """
        return await self.exchange.watch_order_book(symbol, limit)

    async def close(self):
        """Closes the underlying ccxt.pro exchange connection."""
        # The mock exchange also has a 'close' method, so this works for both cases.
        await self.exchange.close()

    async def get_transfer_fees(self, asset: str) -> Dict[str, Any]:
        """
        Fetches deposit and withdrawal fee and network information for a specific asset.
        This uses the synchronous part of the ccxt library, but is wrapped in an
        async method to be consistent with the other provider methods.
        This method works for both real and mock exchanges, as the mock exchange
        also has a 'fetch_deposit_withdraw_fees' method.
        """
        try:
            loop = asyncio.get_running_loop()
            # Use run_in_executor for the synchronous ccxt call
            all_fees = await loop.run_in_executor(
                None, self.exchange.fetch_deposit_withdraw_fees, [asset]
            )

            # Process the structured data
            if asset in all_fees and 'networks' in all_fees[asset]:
                networks = all_fees[asset]['networks']
                return {
                    'asset': asset,
                    'deposit': networks.get('deposit', {}),
                    'withdraw': networks.get('withdraw', {}),
                }
            else:
                return {'asset': asset, 'error': 'No fee info found for asset.'}

        except Exception as e:
            logger.error(f"Could not fetch transfer fees for {asset} from {self.name}: {e}")
            return {'asset': asset, 'error': str(e)}
