"""
导入管理模块 - 统一管理常用的导入语句
"""

# --- Standard Library Imports ---
import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

# --- Third Party Imports ---
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import nest_asyncio

# --- Core Application Imports ---
from src.config import load_config
from src.db import DatabaseManager
from src.engine import ArbitrageEngine, Opportunity

# --- Provider Imports ---
from src.providers.base import BaseProvider
from src.providers.cex import CEXProvider
from src.providers.dex import DEXProvider
from src.providers.bridge import BridgeProvider
from src.providers.free_api import FreeAPIProvider, free_api_provider
from src.providers.ccxt_enhanced import EnhancedCCXTProvider
from src.providers.trend_analyzer import TrendAnalyzer
from src.providers.funding_rate import FundingRateProvider, funding_rate_provider
from src.providers.orderbook_analyzer import OrderBookAnalyzer, orderbook_analyzer
from src.providers.cross_chain_analyzer import CrossChainAnalyzer, cross_chain_analyzer
from src.providers.exchange_health_monitor import ExchangeHealthMonitor, exchange_health_monitor
from src.providers.arbitrage_analyzer import ArbitrageAnalyzer, arbitrage_analyzer
from src.providers.transfer_path_planner import TransferPathPlanner, transfer_path_planner
from src.providers.risk_dashboard import RiskDashboard, risk_dashboard
from src.providers.risk_manager import RiskManager, RiskMetrics, ArbitrageOpportunity

# --- Advanced Provider Imports ---
from src.providers.advanced_arbitrage import (
    AdvancedArbitrageEngine, 
    TriangularArbitrageOpportunity,
    CrossChainOpportunity,
    FuturesSpotOpportunity,
    advanced_arbitrage_engine
)
from src.providers.analytics_engine import (
    AnalyticsEngine,
    PerformanceMetrics,
    BacktestResult,
    analytics_engine
)
from src.providers.market_depth_analyzer import (
    MarketDepthAnalyzer,
    OrderBookSnapshot,
    LiquidityMetrics,
    MarketImpactAnalysis,
    market_depth_analyzer
)
from src.providers.alert_system import (
    AlertSystem,
    AlertType,
    AlertSeverity,
    AlertRule,
    Alert,
    NotificationChannel,
    alert_system
)
from src.providers.account_manager import (
    AccountManager,
    AccountInfo,
    AccountType,
    AccountStatus,
    AllocationStrategy,
    AllocationRule,
    AccountMetrics,
    account_manager
)

# --- UI Imports ---
from src.ui.trading_interface import TradingInterface, trading_interface
from src.ui.components import sidebar_controls, display_error
from src.ui.navigation import render_navigation, render_page_header, render_quick_stats, render_footer

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def setup_streamlit_config():
    """设置Streamlit页面配置"""
    st.set_page_config(
        page_title="主页",
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )

def setup_asyncio():
    """设置异步IO配置"""
    nest_asyncio.apply()