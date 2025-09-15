import streamlit as st
import os
from dotenv import load_dotenv
import yaml

# Load environment variables from a .env file if it exists
load_dotenv()

def load_yaml_config(filepath: str) -> dict:
    """Loads a YAML file and returns its content."""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error(f"Configuration file not found: {filepath}")
        return {}
    except Exception as e:
        st.error(f"Error loading YAML configuration from {filepath}: {e}")
        return {}

def load_config() -> dict:
    """
    Loads configuration from Streamlit secrets and environment variables.
    Streamlit secrets take precedence.
    """
    config = {}

    try:
        # --- Database Configuration ---
        config['db_dsn'] = os.getenv("DB_DSN")
        
        # --- RPC URLs for DEX Providers ---
        config['rpc_urls'] = {
            "ethereum": os.getenv("RPC_URL_ETHEREUM", "https://eth.llamarpc.com"),
            "polygon": os.getenv("RPC_URL_POLYGON", "https://polygon-rpc.com/"),
        }
        
        # --- API Keys for CEX Providers (for authenticated endpoints) ---
        config['api_keys'] = {
            "binance": {
                "apiKey": os.getenv("BINANCE_API_KEY", ""),
                "secret": os.getenv("BINANCE_API_SECRET", ""),
            },
            "coinbase": {
                "apiKey": os.getenv("COINBASE_API_KEY", ""),
                "secret": os.getenv("COINBASE_API_SECRET", ""),
            }
        }
        
        # --- Arbitrage Engine Settings ---
        # Load fee structure from the external YAML file
        fee_config = load_yaml_config('fees.yml')
        config['arbitrage'] = {
            'threshold': 0.2,  # Default threshold, will be overridden by session state in UI
            'fees': fee_config,
            'default_symbols': {
                'bridge': 'BTC.BTC/ETH.ETH',
                'dex': 'WETH/USDC'
            }
        }

        # --- Qualitative Data ---
        config['qualitative_data'] = load_yaml_config('qualitative_data.yml')
        
    except Exception as e:
        st.error(f"配置加载失败: {e}")
        st.info("使用默认配置继续运行...")
        # 提供默认配置以确保应用能够运行
        config = {
            'db_dsn': None,
            'rpc_urls': {
                "ethereum": "https://eth.llamarpc.com",
                "polygon": "https://polygon-rpc.com/",
            },
            'api_keys': {},
            'arbitrage': {
                'threshold': 0.2,
                'fees': {}
            }
        }

    return config
