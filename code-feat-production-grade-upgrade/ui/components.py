import streamlit as st

def sidebar_controls():
    """
    Defines the controls in the sidebar and updates session_state.
    The main app will react to changes in st.session_state.
    """
    st.sidebar.header("⚙️ Configuration")

    # --- Demo Mode Toggle ---
    # This toggle now acts as a read-only status indicator. It is always disabled,
    # and its state is determined automatically by the presence of API keys.
    keys_provided = bool(st.session_state.get('api_keys'))
    st.sidebar.toggle(
        "🚀 Demo Mode",
        value=not keys_provided,
        key='demo_mode',
        help="This is a status indicator. It is automatically turned OFF when you provide API keys.",
        disabled=True  # The toggle is always disabled, making it read-only.
    )
    st.sidebar.divider()

    # --- Exchange Selection ---
    EXCHANGES = ['binance', 'okx', 'bybit', 'kucoin', 'gate', 'mexc', 'bitget', 'htx']
    st.sidebar.multiselect(
        "Select CEX Exchanges",
        options=EXCHANGES,
        default=['binance', 'okx', 'bybit'],
        key='selected_exchanges', # This key links the widget to session_state
        help="Select Centralized Exchanges for ticker and arbitrage analysis."
    )

    # --- API Key Management ---
    st.sidebar.subheader("🔑 API Key Management")
    st.sidebar.caption("API keys are stored in session state and are not saved permanently.")

    # Dynamically create input fields for selected exchanges
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}

    for ex_id in st.session_state.selected_exchanges:
        with st.sidebar.expander(f"{ex_id.capitalize()} API Keys"):
            api_key = st.text_input(f"{ex_id} API Key", key=f"api_key_{ex_id}", value=st.session_state.api_keys.get(ex_id, {}).get('apiKey', ''))
            api_secret = st.text_input(f"{ex_id} API Secret", type="password", key=f"api_secret_{ex_id}", value=st.session_state.api_keys.get(ex_id, {}).get('secret', ''))

            # Update session state as user types
            if api_key and api_secret:
                 st.session_state.api_keys[ex_id] = {'apiKey': api_key, 'secret': api_secret}
            elif ex_id in st.session_state.api_keys:
                 # Clear keys if fields are emptied
                 del st.session_state.api_keys[ex_id]

    st.sidebar.divider()

    # --- Symbol Selection ---
    st.sidebar.multiselect(
        "Select CEX/DEX Symbols",
        options=['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ETH/BTC', 'WETH/USDC', 'WBTC/WETH'],
        default=['BTC/USDT', 'ETH/USDT'],
        key='selected_symbols',
        help="Select symbols to track across exchanges."
    )

    # --- Bridge Symbol Selection ---
    st.sidebar.text_input(
        "Bridge Swap Pair",
        value='BTC.BTC/ETH.ETH',
        key='bridge_symbol',
        help="Enter a cross-chain pair for Thorchain, e.g., 'BTC.BTC/ETH.ETH'."
    )

    # --- Arbitrage Settings ---
    st.sidebar.subheader("Arbitrage Settings")
    st.sidebar.number_input(
        "Profit Threshold (%)",
        min_value=0.01,
        max_value=10.0,
        value=0.2,
        step=0.01,
        key='arbitrage_threshold',
        help="Set the minimum profit percentage to trigger an alert."
    )

    # --- Refresh Control ---
    st.sidebar.subheader("Display Control")
    if st.sidebar.button("🔄 Force Refresh All Data"):
        # Clearing cached resources will force them to rerun
        st.cache_resource.clear()
        st.rerun()

    st.sidebar.toggle("Auto-Refresh", key='auto_refresh_enabled', value=False)
    st.sidebar.number_input(
        "Refresh Interval (s)",
        min_value=5,
        max_value=120,
        value=10,
        step=5,
        key='auto_refresh_interval',
        disabled=not st.session_state.get('auto_refresh_enabled', False)
    )

def display_error(message: str):
    """A standardized way to display errors."""
    st.error(message, icon="🚨")

def display_warning(message: str):
    """A standardized way to display warnings."""
    st.warning(message, icon="⚠️")
