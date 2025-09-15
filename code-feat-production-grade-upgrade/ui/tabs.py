import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import asyncio
from datetime import datetime, timedelta

from providers.cex import CEXProvider
from ui.components import display_error

# --- Tab 1: Real-time Ticker Data ---

def show_realtime_tab(providers, db_manager):
    """Displays the real-time ticker data and saves it to the DB."""
    st.header("📊 Real-time Ticker Data")

    symbols_to_fetch = st.session_state.get('selected_symbols', [])
    if not symbols_to_fetch:
        st.warning("Please select at least one symbol in the sidebar.")
        return

    all_tickers = []

    # Use a placeholder to show loading status
    placeholder = st.empty()
    placeholder.info("Fetching real-time data from all providers...")

    async def fetch_all_tickers():
        tasks = []
        for provider in providers:
            # Determine which symbols the provider should fetch
            # This is a simple check; a more robust app might map providers to symbols
            if isinstance(provider, CEXProvider):
                tasks.extend([provider.get_ticker(s) for s in symbols_to_fetch])
            elif provider.name == "Uniswap V3":
                tasks.extend([provider.get_ticker(s) for s in symbols_to_fetch if s in ['WETH/USDC', 'WBTC/WETH']])
            elif provider.name == "Thorchain":
                tasks.append(provider.get_ticker(st.session_state.bridge_symbol))

        return await asyncio.gather(*tasks, return_exceptions=True)

    results = asyncio.run(fetch_all_tickers())

    for res in results:
        if isinstance(res, dict) and 'error' not in res:
            res['provider_name'] = res.get('provider', 'N/A')
            all_tickers.append(res)

    if not all_tickers:
        placeholder.error("Could not fetch any ticker data. Check provider connections.")
        return

    df = pd.DataFrame(all_tickers)
    df = df[['provider_name', 'symbol', 'last', 'bid', 'ask', 'timestamp']]
    df = df.rename(columns={'provider_name': 'Provider', 'symbol': 'Symbol', 'last': 'Price', 'bid': 'Bid', 'ask': 'Ask'})
    df['Price'] = df['Price'].map('{:,.4f}'.format)

    placeholder.dataframe(df, use_container_width=True, hide_index=True)

    # Save data to DB if enabled
    if db_manager and st.toggle("Save data to DB", value=True):
        # Re-fetch full data for DB schema
        db_records = [t for t in all_tickers if 'error' not in t]
        if db_records:
            asyncio.run(db_manager.save_ticker_data(db_records))
            st.success(f"Saved {len(db_records)} records to the database.")

# --- Tab 2: Market Depth ---

def _create_depth_chart(order_book: dict) -> go.Figure:
    bids = pd.DataFrame(order_book.get('bids', []), columns=['price', 'volume']).astype(float)
    asks = pd.DataFrame(order_book.get('asks', []), columns=['price', 'volume']).astype(float)
    bids = bids.sort_values('price', ascending=False)
    asks = asks.sort_values('price', ascending=True)
    bids['cumulative'] = bids['volume'].cumsum()
    asks['cumulative'] = asks['volume'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bids['price'], y=bids['cumulative'], name='Bids', fill='tozeroy', line_color='green'))
    fig.add_trace(go.Scatter(x=asks['price'], y=asks['cumulative'], name='Asks', fill='tozeroy', line_color='red'))
    fig.update_layout(title_text=f"Market Depth for {order_book.get('symbol', '')}", xaxis_title="Price", yaxis_title="Cumulative Volume")
    return fig

def show_depth_tab(cex_providers):
    st.header("🌊 Market Depth Analysis")
    if not cex_providers:
        st.warning("Please select at least one CEX exchange in the sidebar.")
        return

    col1, col2 = st.columns(2)
    selected_exchange_name = col1.selectbox("Select Exchange", options=[p.name for p in cex_providers])
    symbol = col2.text_input("Enter Symbol", "BTC/USDT", key="depth_symbol")

    if st.button("Fetch Market Depth"):
        provider = next((p for p in cex_providers if p.name == selected_exchange_name), None)
        if not provider:
            st.error("Selected provider not found.")
            return

        with st.spinner(f"Fetching order book for {symbol} from {provider.name}..."):
            try:
                order_book = asyncio.run(provider.get_order_book(symbol, limit=50))
                if 'error' in order_book:
                    display_error(f"Could not fetch order book: {order_book['error']}")
                else:
                    st.plotly_chart(_create_depth_chart(order_book), use_container_width=True)
            except Exception as e:
                display_error(f"An error occurred: {e}")

# --- Tab 3: Arbitrage Opportunities ---

def show_arbitrage_tab(arbitrage_engine):
    st.header("⚡ Arbitrage Opportunities")
    st.info("This tab analyzes price differences across all selected providers to find profitable arbitrage opportunities, accounting for estimated fees.")

    if st.button("Find Arbitrage Opportunities"):
        with st.spinner("Analyzing all pairs and symbols..."):
            try:
                # Update engine with latest threshold from UI
                arbitrage_engine.profit_threshold = st.session_state.get('arbitrage_threshold', 0.2)

                opportunities = asyncio.run(arbitrage_engine.find_opportunities(st.session_state.selected_symbols))

                if not opportunities:
                    st.success("✅ No profitable arbitrage opportunities found with the current settings.")
                else:
                    st.success(f"🎉 Found {len(opportunities)} arbitrage opportunities!")

                    # Create a DataFrame for a clean, sortable, and informative table display
                    df = pd.DataFrame(opportunities)

                    # Format and select columns for the main table
                    display_df = df[[
                        'symbol', 'buy_at', 'sell_at', 'buy_price', 'sell_price',
                        'gross_profit_usd', 'total_fees_usd', 'net_profit_usd', 'profit_percentage'
                    ]]

                    # Improve column names for display
                    display_df.columns = [
                        'Symbol', 'Buy At', 'Sell At', 'Buy Price ($)', 'Sell Price ($)',
                        'Gross Profit ($)', 'Est. Fees ($)', 'Net Profit ($)', 'Net Profit %'
                    ]

                    # Custom styling for numbers
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Buy Price ($)": st.column_config.NumberColumn(format="$%.4f"),
                            "Sell Price ($)": st.column_config.NumberColumn(format="$%.4f"),
                            "Gross Profit ($)": st.column_config.NumberColumn(format="$%.4f"),
                            "Est. Fees ($)": st.column_config.NumberColumn(format="$%.4f"),
                            "Net Profit ($)": st.column_config.NumberColumn(format="$%.4f"),
                            "Net Profit %": st.column_config.NumberColumn(format="%.4f%%"),
                        }
                    )
            except Exception as e:
                display_error(f"An error occurred during arbitrage analysis: {e}")

# --- Tab 4: Historical Analysis ---

def show_history_tab(db_manager):
    st.header("📜 Historical Data Analysis")
    if not db_manager:
        st.warning("Database connection is not available. This feature is disabled.")
        return

    st.info("Query and visualize historical ticker data stored in the database.")

    col1, col2, col3 = st.columns(3)
    symbol = col1.text_input("Symbol", "BTC/USDT", key="history_symbol_input")
    start_date = col2.date_input("Start Date", datetime.now() - timedelta(days=1))
    end_date = col3.date_input("End Date", datetime.now())

    if st.button("Query Historical Data"):
        if not symbol:
            st.warning("Please enter a symbol.")
            return

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        with st.spinner(f"Querying data for {symbol} from {start_date} to {end_date}..."):
            try:
                df = asyncio.run(db_manager.query_historical_data(symbol, start_datetime, end_datetime))
                if df.empty:
                    st.success("No historical data found for the selected criteria.")
                else:
                    st.dataframe(df, use_container_width=True)
                    # Create a simple price chart
                    fig = go.Figure()
                    for provider in df['provider_name'].unique():
                        provider_df = df[df['provider_name'] == provider]
                        fig.add_trace(go.Scatter(x=provider_df['timestamp'], y=provider_df['price'], mode='lines', name=provider))
                    fig.update_layout(title=f"Price History for {symbol}", xaxis_title="Timestamp", yaxis_title="Price (USD)")
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                display_error(f"An error occurred while querying the database: {e}")

# --- Tab 5: Transfer Fee Comparison ---

def show_fees_tab(cex_providers):
    """Displays a tab for comparing deposit and withdrawal fees across exchanges."""
    st.header("💸 Transfer Fee Comparison")
    st.info("Compare deposit and withdrawal fees and available networks for a specific asset across all selected CEXs.")

    if not cex_providers:
        st.warning("Please select at least one CEX exchange in the sidebar.")
        return

    asset = st.text_input("Enter Asset Symbol to Compare", "USDT", key="fee_asset_input").upper()

    if st.button("Compare Transfer Fees"):
        if not asset:
            st.warning("Please enter an asset symbol.")
            return

        async def fetch_all_fees():
            # Use the new get_transfer_fees method
            tasks = [provider.get_transfer_fees(asset) for provider in cex_providers]
            return await asyncio.gather(*tasks, return_exceptions=True)

        with st.spinner(f"Fetching transfer fees for {asset} from all selected exchanges..."):
            results = asyncio.run(fetch_all_fees())

        processed_data = []
        failed_providers = []
        for i, res in enumerate(results):
            provider_name = cex_providers[i].name
            if isinstance(res, dict) and 'error' not in res:
                # Process deposits
                for network, details in res.get('deposit', {}).items():
                    processed_data.append({
                        'Exchange': provider_name.capitalize(),
                        'Type': 'Deposit',
                        'Asset': asset,
                        'Network': network,
                        'Fee': details.get('fee', 0.0),
                        'Is Percentage': details.get('percentage', False)
                    })
                # Process withdrawals
                for network, details in res.get('withdraw', {}).items():
                    processed_data.append({
                        'Exchange': provider_name.capitalize(),
                        'Type': 'Withdrawal',
                        'Asset': asset,
                        'Network': network,
                        'Fee': details.get('fee'),
                        'Is Percentage': details.get('percentage', False)
                    })
            else:
                # Collect names of providers that failed
                failed_providers.append(provider_name.capitalize())

        # Display a single error message for all failed providers
        if failed_providers:
            st.error(f"Could not fetch fee data for the following exchanges: {', '.join(failed_providers)}. They may not support the asset '{asset}' or the API may be unavailable.")

        if not processed_data:
            st.warning("No fee data was successfully fetched for any exchange.")
        else:
            df = pd.DataFrame(processed_data)
            df = df[['Exchange', 'Type', 'Network', 'Fee', 'Is Percentage', 'Asset']]
            st.dataframe(df, use_container_width=True, hide_index=True)

# --- Tab 6: Qualitative Exchange Comparison ---

def show_comparison_tab(qualitative_data: dict):
    """Displays a tab for comparing qualitative data about exchanges."""
    st.header("🏢 Exchange Comparison")
    st.info("View manually compiled information about different exchanges.")

    if not qualitative_data:
        st.warning("No qualitative data was found. Check the `qualitative_data.yml` file.")
        return

    exchange_list = list(qualitative_data.keys())
    selected_exchange = st.selectbox(
        "Select an Exchange to View Details",
        options=exchange_list,
        format_func=lambda x: x.capitalize()
    )

    if selected_exchange:
        data = qualitative_data[selected_exchange]
        st.subheader(f"Details for {selected_exchange.capitalize()}")

        # Define the order of keys for a more consistent layout
        key_order = [
            'security_measures', 'customer_service', 'platform_stability',
            'fund_insurance', 'regional_restrictions', 'withdrawal_limits',
            'withdrawal_speed', 'supported_cross_chain_bridges',
            'api_support_details', 'fee_discounts', 'margin_leverage_details',
            'maintenance_schedule', 'user_rating_summary', 'tax_compliance_info'
        ]

        # Create a two-column layout for better readability
        col1, col2 = st.columns(2)

        # Distribute the items into two columns
        for i, key in enumerate(key_order):
            if key in data:
                display_key = key.replace('_', ' ').capitalize()
                value = data[key]

                # Alternate between columns
                if i % 2 == 0:
                    with col1:
                        st.markdown(f"**{display_key}**")
                        st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>{value}</div>", unsafe_allow_html=True)
                else:
                    with col2:
                        st.markdown(f"**{display_key}**")
                        st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>{value}</div>", unsafe_allow_html=True)
