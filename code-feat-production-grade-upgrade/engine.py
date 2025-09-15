import asyncio
from typing import List, Dict, Any
import itertools

class ArbitrageEngine:
    """
    Analyzes real-time data from multiple providers to find arbitrage opportunities.
    """
    def __init__(self, providers: List, config: Dict):
        """
        Initializes the engine with data providers and configuration.

        Args:
            providers: A list of instantiated provider objects.
            config: A dictionary containing 'fees' and 'threshold' settings.
        """
        self.providers = providers
        # Example fee structure: {'binance': {'taker': 0.001, 'withdrawal_usd': 5}}
        self.fees_config = config.get('fees', {})
        self.profit_threshold = config.get('threshold', 0.001) # Default 0.1%

    async def find_opportunities(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Compares prices across all providers for given symbols and
        identifies potential arbitrage opportunities after fees.

        Args:
            symbols: A list of symbols to check for arbitrage, e.g., ['BTC/USDT', 'ETH/USDT'].

        Returns:
            A list of dictionaries, where each dictionary represents a
            profitable arbitrage opportunity.
        """
        all_opportunities = []
        for symbol in symbols:
            # Fetch tickers from all providers concurrently
            tasks = [provider.get_ticker(symbol) for provider in self.providers]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out errors and create a list of valid tickers
            valid_tickers = []
            for i, res in enumerate(results):
                if isinstance(res, dict) and 'error' not in res and res.get('ask') and res.get('bid'):
                    # Add provider name to the ticker info
                    res['provider_name'] = self.providers[i].name
                    valid_tickers.append(res)
                # else:
                #     print(f"Skipping invalid ticker from {self.providers[i].name}: {res}")

            if len(valid_tickers) < 2:
                continue # Need at least two providers to find an opportunity

            # Find the best buy (lowest ask) and sell (highest bid) prices
            # We check all possible pairs of exchanges
            for buy_ticker, sell_ticker in itertools.permutations(valid_tickers, 2):

                buy_provider_name = buy_ticker['provider_name']
                sell_provider_name = sell_ticker['provider_name']

                buy_price = float(buy_ticker['ask']) # Price to buy at
                sell_price = float(sell_ticker['bid']) # Price to sell at

                if buy_price >= sell_price:
                    continue # No potential for profit

                # --- Fee Calculation ---
                # Get fee info for the two providers, using defaults if not found
                default_fees = self.fees_config.get('default', {})
                buy_fees = self.fees_config.get(buy_provider_name.lower(), default_fees)
                sell_fees = self.fees_config.get(sell_provider_name.lower(), default_fees)

                # 1. Cost of buying 1 unit of the base asset
                initial_cost_usd = buy_price
                buy_fee_usd = initial_cost_usd * buy_fees.get('taker', 0.002)
                total_cost_usd = initial_cost_usd + buy_fee_usd

                # 2. Revenue from selling 1 unit of the base asset
                revenue_usd = sell_price
                sell_fee_usd = revenue_usd * sell_fees.get('taker', 0.002)
                net_revenue_usd = revenue_usd - sell_fee_usd

                # 3. Withdrawal fee calculation (more accurate model)
                base_asset = symbol.split('/')[0]
                withdrawal_fees_map = buy_fees.get('withdrawal_fees', {})

                # Get the fee for the specific asset, or a default if not specified
                withdrawal_fee_asset_amount = withdrawal_fees_map.get(base_asset, 0.0)

                # Convert the asset withdrawal fee to its USD equivalent using the buy price
                withdrawal_fee_usd = withdrawal_fee_asset_amount * buy_price

                # 4. Calculate Net Profit
                net_profit_usd = net_revenue_usd - total_cost_usd - withdrawal_fee_usd

                if net_profit_usd <= 0:
                    continue

                profit_percentage = (net_profit_usd / total_cost_usd) * 100

                if profit_percentage > self.profit_threshold:
                    gross_profit_usd = sell_price - buy_price
                    total_fees_usd = buy_fee_usd + sell_fee_usd + withdrawal_fee_usd

                    opportunity = {
                        'symbol': symbol,
                        'buy_at': buy_provider_name,
                        'sell_at': sell_provider_name,
                        'buy_price': round(buy_price, 4),
                        'sell_price': round(sell_price, 4),
                        'gross_profit_usd': round(gross_profit_usd, 4),
                        'total_fees_usd': round(total_fees_usd, 4),
                        'net_profit_usd': round(net_profit_usd, 4),
                        'profit_percentage': round(profit_percentage, 4),
                    }
                    all_opportunities.append(opportunity)

        return all_opportunities
