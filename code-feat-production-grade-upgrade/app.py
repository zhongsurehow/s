import streamlit as st
import asyncio
import nest_asyncio
import time
import logging

# --- Basic Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from config import load_config
from db import DatabaseManager
from engine import ArbitrageEngine
from providers.cex import CEXProvider
from providers.dex import DEXProvider
from providers.bridge import BridgeProvider
from ui.tabs import show_realtime_tab, show_depth_tab, show_arbitrage_tab, show_history_tab
from ui.components import sidebar_controls

# Apply nest_asyncio to allow running asyncio event loops within Streamlit's loop
# This is crucial for integrating async libraries with Streamlit
nest_asyncio.apply()

st.set_page_config(
    page_title="数字货币交易所对比工具 (生产级)",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- App Title ---
st.markdown("<h1>🚀 数字货币交易所对比工具 (生产级)</h1>", unsafe_allow_html=True)

# --- Initialization & Caching ---

@st.cache_data
def get_config():
    """Load configuration from file and cache it."""
    return load_config()

@st.cache_resource
def get_db_manager(dsn):
    """Create and cache the database manager and its connection pool."""
    if not dsn:
        st.warning("Database DSN not configured. Historical analysis will be disabled.")
        return None
    try:
        db_manager = DatabaseManager(dsn)
        asyncio.run(db_manager.connect())
        asyncio.run(db_manager.init_db())
        return db_manager
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

@st.cache_resource
def get_providers(_config, _session_state):
    """
    Create and cache a list of all data providers based on the current mode (Demo or Real).
    This function is made resilient to individual provider failures.
    """
    providers = []
    is_demo_mode = _session_state.get('demo_mode', True)

    # Prepare a unified config for providers, prioritizing UI keys over file-based keys
    provider_config = _config.copy()
    file_keys = _config.get('api_keys', {})
    ui_keys = _session_state.get('api_keys', {})
    merged_keys = {**file_keys, **ui_keys}
    provider_config['api_keys'] = merged_keys

    # CEX Providers
    for ex_id in _session_state.selected_exchanges:
        try:
            # Pass the merged config and the demo mode flag to the provider
            providers.append(CEXProvider(name=ex_id, config=provider_config, force_mock=is_demo_mode))
        except Exception as e:
            st.warning(f"Failed to initialize CEX provider '{ex_id}': {e}", icon="⚠️")

    if is_demo_mode:
        st.info("DEX and Bridge providers are disabled in Demo Mode.", icon="ℹ️")
    else:
        # DEX Providers (only initialize in real data mode)
        try:
            if _config.get('rpc_urls', {}).get('ethereum'):
                providers.append(DEXProvider(name="Uniswap V3", rpc_url=_config['rpc_urls']['ethereum']))
            else:
                st.warning("Ethereum RPC URL not configured. DEX provider is disabled.", icon="⚠️")
        except Exception as e:
            st.warning(f"Failed to initialize DEX provider 'Uniswap V3': {e}", icon="⚠️")

        # Bridge Providers (only initialize in real data mode)
        try:
            providers.append(BridgeProvider(name="Thorchain"))
        except Exception as e:
            st.warning(f"Failed to initialize Bridge provider 'Thorchain': {e}", icon="⚠️")

    return providers

def init_session_state(config):
    """Initializes the session state with default values from the config."""
    default_symbols = config.get('arbitrage', {}).get('default_symbols', {})
    if 'bridge_symbol' not in st.session_state:
        st.session_state.bridge_symbol = default_symbols.get('bridge', 'BTC.BTC/ETH.ETH')
    if 'dex_symbol' not in st.session_state:
        st.session_state.dex_symbol = default_symbols.get('dex', 'WETH/USDC')
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}
    if 'selected_exchanges' not in st.session_state:
        st.session_state.selected_exchanges = ['binance', 'okx', 'bybit']

# --- Main App Logic ---
def main():
    config = get_config()
    init_session_state(config)

    # The sidebar must be rendered first to initialize all its widgets and session state keys
    sidebar_controls()

    # Initialize managers
    db_manager = get_db_manager(config.get("db_dsn"))

    # Get providers based on current selection in session state
    # Pass session_state explicitly because it's used as part of the cache key for get_providers
    providers = get_providers(config, st.session_state)

    # Initialize arbitrage engine
    arbitrage_engine = ArbitrageEngine(providers, config.get('arbitrage', {}))

    # Main content area with tabs
    tab_names = ["实时行情", "市场深度", "套利机会", "费用对比", "交易所对比", "历史分析"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_names)

    with tab1:
        show_realtime_tab(providers, db_manager)

    with tab2:
        # Pass only CEX providers to the depth tab
        cex_providers = [p for p in providers if isinstance(p, CEXProvider)]
        show_depth_tab(cex_providers)

    with tab3:
        show_arbitrage_tab(arbitrage_engine)

    with tab4:
        from ui.tabs import show_fees_tab
        cex_providers = [p for p in providers if isinstance(p, CEXProvider)]
        show_fees_tab(cex_providers)

    with tab5:
        from ui.tabs import show_comparison_tab
        show_comparison_tab(config.get('qualitative_data', {}))

    with tab6:
        show_history_tab(db_manager)


if __name__ == "__main__":
    main()

    # --- Auto-refresh loop ---
    if st.session_state.get('auto_refresh_enabled', False):
        interval = st.session_state.get('auto_refresh_interval', 10)
        time.sleep(interval)
        st.rerun()
