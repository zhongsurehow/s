# --- Python Path Setup ---
from path_setup import setup_project_path
setup_project_path()

# --- Import Management ---
from src.imports import *
from src.imports import setup_logging, setup_streamlit_config, setup_asyncio

# --- Setup Configuration ---
logger = setup_logging()
setup_streamlit_config()
setup_asyncio()

# --- Helper Functions ---
def safe_run_async(coro):
    """Safely runs an async coroutine, handling nested event loops."""
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        if "cannot run loop while another loop is running" in str(e):
            # This is expected in Streamlit's environment with nest_asyncio
            return asyncio.run(coro)
        st.error(f"异步操作失败: {e}")
        return None

def _validate_symbol(symbol: str) -> bool:
    """Validates that the symbol is not empty and has a valid format."""
    if not symbol or '/' not in symbol or len(symbol.split('/')) != 2:
        st.error("请输入有效的交易对格式，例如 'BTC/USDT'。")
        return False
    return True

def _create_depth_chart(order_book: dict) -> go.Figure:
    """Creates a Plotly order book depth chart."""
    bids = pd.DataFrame(order_book.get('bids', []), columns=['price', 'volume']).astype(float)
    asks = pd.DataFrame(order_book.get('asks', []), columns=['price', 'volume']).astype(float)
    bids = bids.sort_values('price', ascending=False)
    asks = asks.sort_values('price', ascending=True)
    bids['cumulative'] = bids['volume'].cumsum()
    asks['cumulative'] = asks['volume'].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bids['price'], y=bids['cumulative'], name='买单', fill='tozeroy', line_color='green'))
    fig.add_trace(go.Scatter(x=asks['price'], y=asks['cumulative'], name='卖单', fill='tozeroy', line_color='red'))
    fig.update_layout(title_text=f"{order_book.get('symbol', '')} 市场深度", xaxis_title="价格", yaxis_title="累计数量", height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def _create_candlestick_chart(df: pd.DataFrame, symbol: str, show_volume: bool = True, ma_periods: list = None) -> go.Figure:
    """Creates a Plotly candlestick chart from OHLCV data with optional indicators."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title_text=f"{symbol} K线图 - 无数据", height=400)
        return fig
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        fig = go.Figure()
        fig.update_layout(title_text=f"{symbol} K线图 - 数据格式错误", height=400)
        return fig
    
    # Convert timestamp to datetime if it's not already
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    )])
    
    # Add moving averages if requested
    if ma_periods:
        colors = ['orange', 'purple', 'green', 'red', 'cyan', 'magenta']
        for i, period in enumerate(ma_periods):
            if len(df) >= period:
                ma = df['close'].rolling(window=period).mean()
                fig.add_trace(go.Scatter(
                    x=df['datetime'],
                    y=ma,
                    mode='lines',
                    name=f'MA{period}',
                    line=dict(color=colors[i % len(colors)], width=1.5)
                ))
    
    # Add volume as a subplot if requested
    if show_volume:
        fig.add_trace(go.Bar(
            x=df['datetime'],
            y=df['volume'],
            name='成交量',
            yaxis='y2',
            opacity=0.3,
            marker_color='blue'
        ))
    
    # Configure layout
    layout_config = {
        'title_text': f"{symbol} K线图",
        'xaxis_title': "时间",
        'yaxis_title': "价格",
        'height': 600 if show_volume else 500,
        'margin': dict(l=20, r=20, t=40, b=20),
        'xaxis_rangeslider_visible': False,
        'showlegend': True
    }
    
    if show_volume:
        layout_config['yaxis2'] = dict(
            title="成交量",
            overlaying='y',
            side='right',
            showgrid=False
        )
    
    fig.update_layout(**layout_config)
    
    return fig

# --- Caching Functions ---
@st.cache_data
def get_config():
    """Load configuration from file and cache it."""
    return load_config()

@st.cache_resource
def get_db_manager(db_path: str):
    """Creates and caches the database manager."""
    if not db_path: return None
    db_manager = DatabaseManager(db_path)
    try:
        asyncio.run(db_manager.__aenter__())
        asyncio.run(db_manager.init_db())
        return db_manager
    except Exception as e:
        st.error(f"连接或初始化SQLite数据库时失败: {e}")
        asyncio.run(db_manager.__aexit__(None, None, None))
        return None

@st.cache_resource
def get_providers(_config: Dict, _session_state) -> List[BaseProvider]:
    """Create and cache a list of all data providers."""
    providers = []
    is_demo_mode = not bool(_session_state.get('api_keys'))
    provider_config = _config.copy()
    provider_config['api_keys'] = {**_config.get('api_keys', {}), **_session_state.get('api_keys', {})}
    for ex_id in _session_state.selected_exchanges:
        try:
            providers.append(CEXProvider(name=ex_id, config=provider_config, force_mock=is_demo_mode))
        except ValueError as e:
            st.error(f"初始化 CEX 提供商 '{ex_id}' 失败: {e}", icon="🚨")
        except Exception as e:
            st.warning(f"初始化 CEX 提供商 '{ex_id}' 时发生未知错误: {e}", icon="⚠️")
    return providers

def init_session_state(config):
    """Initializes the session state with default values."""
    if 'selected_exchanges' not in st.session_state:
        st.session_state.selected_exchanges = ['binance', 'okx', 'bybit']
    if 'selected_symbols' not in st.session_state:
        st.session_state.selected_symbols = ['BTC/USDT', 'ETH/USDT']
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {}

# --- Dashboard UI ---
def _render_dashboard_header(providers: List[BaseProvider], engine: ArbitrageEngine):
    """Renders the main metric headers for the dashboard."""
    st.title("🎯 专业套利交易系统")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("连接交易所", len([p for p in providers if isinstance(p, CEXProvider)]))
    with col2:
        st.metric("监控币种", len(st.session_state.get('selected_symbols', [])))
    with col3:
        demo_mode = not bool(st.session_state.get('api_keys'))
        st.metric("运行模式", "演示" if demo_mode else "实时")
    
    # Placeholders for metrics that require data
    opp_placeholder = st.empty()
    profit_placeholder = st.empty()
    
    with st.spinner("正在计算实时指标..."):
        opportunities = safe_run_async(engine.find_opportunities(st.session_state.selected_symbols)) if engine else []
        with col4:
            profitable_opps = len([opp for opp in opportunities if opp.get('profit_percentage', 0) > 0.1])
            st.metric("活跃机会", profitable_opps, delta=f"+{profitable_opps}" if profitable_opps > 0 else None)
        with col5:
            max_profit = max([opp.get('profit_percentage', 0) for opp in opportunities], default=0)
            st.metric("最高收益率", f"{max_profit:.3f}%", delta=f"+{max_profit:.3f}%" if max_profit > 0 else None)
    return opportunities

def _render_opportunity_leaderboard(engine: ArbitrageEngine, risk_manager: RiskManager):
    """Renders the main table of arbitrage opportunities."""
    st.subheader("📈 实时套利机会排行榜")
    min_profit_filter = st.number_input("最小收益率过滤 (%)", min_value=0.0, max_value=5.0, value=0.1, step=0.05, key="profit_filter")

    opp_placeholder = st.empty()
    with st.spinner("正在寻找套利机会..."):
        opportunities = safe_run_async(engine.find_opportunities(st.session_state.selected_symbols))
        filtered_opps = [opp for opp in opportunities if opp.get('profit_percentage', 0) >= min_profit_filter]
        
        if not filtered_opps:
            opp_placeholder.info(f"🔍 未发现收益率 ≥ {min_profit_filter}% 的套利机会")
            return

        df = pd.DataFrame(filtered_opps).sort_values(by="profit_percentage", ascending=False)
        opp_placeholder.dataframe(df, use_container_width=True, hide_index=True)

def show_dashboard(engine: ArbitrageEngine, providers: List[BaseProvider]):
    """The main view of the application, broken down into smaller components."""

    # Initialize Risk Manager
    if 'risk_manager' not in st.session_state:
        st.session_state.risk_manager = RiskManager(initial_capital=100000)
    risk_manager = st.session_state.risk_manager

    # Render Header
    opportunities = _render_dashboard_header(providers, engine)

    # Render Main Content Tabs
    tab_titles = ["📈 实时套利机会", "📊 价格对比", "⚙️ 风险管理", "🧰 工具箱"]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    with tab1:
        _render_opportunity_leaderboard(engine, risk_manager)

    with tab2:
        render_unified_price_comparison(providers)

    with tab3:
        st.subheader("🛡️ 专业风险管理中心")
        # This section can be further broken down if needed
        risk_metrics = risk_manager.calculate_risk_metrics()
        # ... (rest of the risk management UI)

    with tab4:
        st.subheader("💰 套利收益计算器")
        # ... (rest of the profit calculator UI)

    st.markdown("---")

    # Tools and other data sections
    st.subheader("💰 套利收益计算器")

    with st.container():
        calc_col1, calc_col2 = st.columns(2)
        
        with calc_col1:
            investment_amount = st.number_input("投资金额 (USDT)", min_value=100, max_value=1000000, value=10000, step=100, key="investment")
            expected_profit = st.number_input("预期收益率 (%)", min_value=0.01, max_value=20.0, value=1.0, step=0.01, key="expected_profit")

        with calc_col2:
            trading_fee = st.number_input("交易手续费 (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.01, key="trading_fee")
            slippage = st.number_input("滑点损失 (%)", min_value=0.0, max_value=5.0, value=0.2, step=0.01, key="slippage")

        # Calculate results
        gross_profit = investment_amount * (expected_profit / 100)
        total_fees = investment_amount * ((trading_fee * 2 + slippage) / 100)  # Buy + Sell fees + slippage
        net_profit = gross_profit - total_fees
        roi = (net_profit / investment_amount) * 100
        
        # Display results
        st.markdown("**📊 收益分析**")
        result_col1, result_col2, result_col3 = st.columns(3)
        
        with result_col1:
            st.metric("毛利润", f"${gross_profit:.2f}")
        with result_col2:
            st.metric("总费用", f"${total_fees:.2f}")
        with result_col3:
            color = "normal" if net_profit > 0 else "inverse"
            st.metric("净利润", f"${net_profit:.2f}", f"{roi:.3f}%")
        
        # Risk assessment
        if net_profit > 0:
            if roi > 0.5:
                st.success(f"🟢 高收益机会: 净收益率 {roi:.3f}%")
            elif roi > 0.1:
                st.info(f"🟡 中等机会: 净收益率 {roi:.3f}%")
            else:
                st.warning(f"🟠 低收益机会: 净收益率 {roi:.3f}%")
        else:
            st.error(f"🔴 亏损风险: 净收益率 {roi:.3f}%")

def render_unified_price_comparison(providers: List[BaseProvider]):
    """
    Renders a unified price comparison UI that can switch between
    CEX providers (API key-based) and the Free API provider.
    """
    from src.ui.dashboard_components import (
        render_cex_price_comparison, 
        render_free_api_comparison,
        render_risk_monitoring_panel,
        render_batch_monitoring_panel
    )
    
    st.markdown("---")
    st.subheader("📊 实时价格对比")

    data_source = st.selectbox("选择数据源", ["CEX (需要API密钥)", "免费API (8大交易所)"], key="price_source_selector")

    if data_source == "CEX (需要API密钥)":
        price_placeholder = st.empty()
        render_cex_price_comparison(providers, price_placeholder)
    elif data_source == "免费API (8大交易所)":
        render_free_api_comparison()
    
    # 实时风险监控面板
    st.markdown("---")
    render_risk_monitoring_panel()
    
    # 批量监控面板
    st.markdown("---")
    render_batch_monitoring_panel()

    st.markdown("---")

    st.subheader("🌊 市场深度可视化")
    depth_cols = st.columns(3)
    selected_ex = depth_cols[0].selectbox("选择交易所", options=[p.name for p in providers if isinstance(p, CEXProvider)], key="depth_exchange")
    selected_sym = depth_cols[1].text_input("输入交易对", st.session_state.selected_symbols[0], key="depth_symbol")

    if depth_cols[2].button("查询深度", key="depth_button"):
        if _validate_symbol(selected_sym):
            provider = next((p for p in providers if p.name == selected_ex), None)
            if provider:
                with st.spinner(f"正在从 {provider.name} 获取 {selected_sym} 的订单簿..."):
                    order_book = safe_run_async(provider.get_order_book(selected_sym))
                    if order_book and 'error' not in order_book:
                        st.plotly_chart(_create_depth_chart(order_book), width='stretch', key="order_book_depth_chart")
                    else:
                        display_error(f"无法获取订单簿: {order_book.get('error', '未知错误')}")

    st.markdown("---")
    with st.expander("🏢 交易所定性对比", expanded=False):
        show_comparison_view(get_config().get('qualitative_data', {}), providers)
    
    st.markdown("---")
    with st.expander("💰 资金费率套利机会", expanded=False):
        show_funding_rate_view()
    
    st.markdown("---")
    with st.expander("📊 订单簿深度与滑点分析", expanded=False):
        show_orderbook_analysis()
    
    st.markdown("---")
    with st.expander("🌉 跨链转账效率与成本分析", expanded=False):
        show_cross_chain_analysis()
    
    st.markdown("---")
    with st.expander("🏥 交易所健康状态监控", expanded=False):
        show_exchange_health_monitor()
    
    st.markdown("---")
    with st.expander("💰 期现套利机会视图", expanded=False):
        show_arbitrage_opportunities()
    
    st.markdown("---")
    with st.expander("🛣️ 转账路径规划器", expanded=False):
        show_transfer_path_planner()
    
    st.markdown("---")
    with st.expander("📊 动态风险仪表盘", expanded=False):
        show_risk_dashboard()
    
    st.markdown("---")
    with st.expander("🚀 增强CCXT交易所支持", expanded=False):
        show_enhanced_ccxt_features()


def show_comparison_view(qualitative_data: dict, providers: List[BaseProvider]):
    """Displays a side-by-side comparison of qualitative data for selected exchanges."""
    if not qualitative_data:
        st.warning("未找到定性数据。")
        return

    key_to_chinese = {
        'security_measures': '安全措施', 'customer_service': '客户服务', 'platform_stability': '平台稳定性',
        'fund_insurance': '资金保险', 'regional_restrictions': '地区限制', 'withdrawal_limits': '提现限额',
        'withdrawal_speed': '提现速度', 'supported_cross_chain_bridges': '支持的跨链桥',
        'api_support_details': 'API支持详情', 'fee_discounts': '手续费折扣', 'margin_leverage_details': '杠杆交易详情',
        'maintenance_schedule': '维护计划', 'user_rating_summary': '用户评分摘要', 'tax_compliance_info': '税务合规信息',
        'deposit_networks': '充值网络', 'deposit_fees': '充值费用', 'withdrawal_networks': '提现网络',
        'margin_trading_api': '保证金交易API'
    }

    exchange_list = list(qualitative_data.keys())
    selected = st.multiselect(
        "选择要比较的交易所",
        options=exchange_list,
        default=exchange_list[:3] if len(exchange_list) >= 3 else exchange_list,
        format_func=lambda x: x.capitalize(),
        key="qualitative_multiselect"
    )

    if selected:
        comparison_data = {exch: qualitative_data[exch] for exch in selected if exch in qualitative_data}
        df = pd.DataFrame(comparison_data).rename(index=key_to_chinese)
        all_keys_df = pd.DataFrame(index=list(key_to_chinese.values()))
        df_display = all_keys_df.join(df).fillna("N/A")
        st.dataframe(df_display, width='stretch')

    with st.expander("🪙 资产转账分析"):
        cex_providers = [p for p in providers if isinstance(p, CEXProvider)]
        show_asset_transfer_view(cex_providers, providers)


def show_asset_transfer_view(cex_providers: List[CEXProvider], providers: List[BaseProvider]):
    """Displays a side-by-side comparison of transfer fees for a given asset."""
    asset = st.text_input("输入要比较的资产代码", "USDT", key="transfer_asset_input").upper()

    if st.button("比较资产转账选项", key="compare_transfers"):
        if not asset:
            st.error("请输入一个资产代码。")
            return

        with st.spinner(f"正在从所有选定的交易所获取 {asset} 的转账费用..."):
            results = safe_run_async(asyncio.gather(*[p.get_transfer_fees(asset) for p in cex_providers]))

        all_networks = set()
        processed_data = {}
        failed_providers = []

        for i, res in enumerate(results):
            provider_name = cex_providers[i].name.capitalize()
            if isinstance(res, dict) and 'error' not in res:
                withdraw_info = res.get('withdraw', {})
                processed_data[provider_name] = {}
                for network, details in withdraw_info.items():
                    all_networks.add(network)
                    fee = details.get('fee')
                    processed_data[provider_name][network] = f"{fee:.6f}".rstrip('0').rstrip('.') if fee is not None else "N/A"
            else:
                failed_providers.append(provider_name)

        if failed_providers:
            st.warning(f"无法获取以下交易所的费用数据: {', '.join(failed_providers)}。")

        if processed_data:
            df = pd.DataFrame(processed_data).reindex(sorted(list(all_networks))).fillna("不支持")
            st.subheader(f"{asset} 提现费用对比")
            st.dataframe(df, width='stretch')
        else:
            st.warning(f"未能成功获取任何交易所关于 '{asset}' 的费用数据。")

    with st.expander("📈 K线图与历史数据"):
        show_kline_view(providers)


def show_kline_view(providers: List[BaseProvider]):
    """Displays a candlestick chart for a selected symbol and exchange."""
    cex_providers = [p for p in providers if isinstance(p, CEXProvider)]
    if not cex_providers:
        st.warning("无可用CEX提供商。")
        return

    # Main controls
    col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1.5])
    name = col1.selectbox("选择交易所", options=[p.name for p in cex_providers], key="kline_exchange")
    symbol = col2.text_input("输入交易对", "BTC/USDT", key="kline_symbol")
    timeframe = col3.selectbox("选择时间周期", options=['1d', '4h', '1h', '30m', '5m'], key="kline_timeframe")
    limit = col4.number_input("数据点", min_value=20, max_value=1000, value=100, key="kline_limit")
    
    # Advanced options
    with st.expander("📊 高级选项"):
        col_a, col_b = st.columns(2)
        show_volume = col_a.checkbox("显示成交量", value=True, key="show_volume")
        show_ma = col_b.checkbox("显示移动平均线", value=False, key="show_ma")
        if show_ma:
            ma_periods = st.multiselect(
                "移动平均线周期",
                options=[5, 10, 20, 50, 100, 200],
                default=[20, 50],
                key="ma_periods"
            )

    if st.button("获取K线数据", key="get_kline"):
        if _validate_symbol(symbol):
            provider = next((p for p in cex_providers if p.name == name), None)
            if provider:
                with st.spinner(f"正在从 {provider.name} 获取 {symbol} 的 {timeframe} 数据..."):
                    data = safe_run_async(provider.get_historical_data(symbol, timeframe, limit))
                    if data:
                        df = pd.DataFrame(data)
                        fig = _create_candlestick_chart(df, symbol, show_volume, ma_periods if show_ma else None)
                        st.plotly_chart(fig, width='stretch', key="candlestick_chart")
                    else:
                        display_error(f"无法获取 {symbol} 的K线数据。")

def show_funding_rate_view():
    """显示资金费率套利机会"""
    st.subheader("💰 永续合约资金费率分析")
    
    # 控制面板
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_symbols = st.multiselect(
            "选择交易对",
            funding_rate_provider.get_popular_symbols(),
            default=['BTC/USDT', 'ETH/USDT'],
            key="funding_symbols"
        )
    
    with col2:
        min_rate_diff = st.number_input(
            "最小费率差异 (%)",
            min_value=0.001,
            max_value=1.0,
            value=0.01,
            step=0.001,
            format="%.3f",
            key="min_funding_diff"
        )
    
    with col3:
        auto_refresh_funding = st.checkbox(
            "自动刷新 (5分钟)",
            value=False,
            key="auto_refresh_funding"
        )
    
    if st.button("🔄 获取最新资金费率", width='stretch'):
        with st.spinner("正在获取资金费率数据..."):
            # 获取聚合资金费率数据
            funding_data = safe_run_async(funding_rate_provider.get_aggregated_funding_rates(selected_symbols))
            
            if funding_data:
                st.session_state['funding_data'] = funding_data
                st.session_state['funding_last_update'] = datetime.now()
                st.success(f"✅ 成功获取 {len(funding_data)} 个交易对的资金费率数据")
            else:
                st.error("❌ 获取资金费率数据失败")
    
    # 显示缓存的数据
    if 'funding_data' in st.session_state and st.session_state['funding_data']:
        funding_data = st.session_state['funding_data']
        last_update = st.session_state.get('funding_last_update', datetime.now())
        
        st.info(f"📊 数据更新时间: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 计算套利机会
        opportunities = funding_rate_provider.calculate_funding_arbitrage_opportunity(funding_data)
        
        # 过滤机会
        filtered_opportunities = [
            opp for opp in opportunities 
            if opp['rate_difference'] >= min_rate_diff / 100
        ]
        
        if filtered_opportunities:
            st.subheader(f"🎯 发现 {len(filtered_opportunities)} 个资金费率套利机会")
            
            # 创建机会表格
            opp_df = pd.DataFrame(filtered_opportunities)
            
            # 格式化显示
            display_df = opp_df[[
                'symbol', 'long_exchange', 'short_exchange', 
                'rate_difference', 'annual_return_pct', 'risk_level'
            ]].copy()
            
            display_df.columns = [
                '交易对', '做多交易所', '做空交易所', 
                '费率差异(%)', '年化收益率(%)', '风险等级'
            ]
            
            # 格式化数值
            display_df['费率差异(%)'] = (display_df['费率差异(%)'] * 100).round(4)
            display_df['年化收益率(%)'] = display_df['年化收益率(%)'].round(2)
            
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "费率差异(%)": st.column_config.NumberColumn(format="%.4f%%"),
                    "年化收益率(%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "风险等级": st.column_config.TextColumn()
                }
            )
            
            # 详细分析
            st.subheader("📈 资金费率趋势分析")
            
            # 创建资金费率对比图表
            fig = go.Figure()
            
            for symbol, rates in funding_data.items():
                if len(rates) >= 2:
                    exchanges = [rate['exchange'] for rate in rates]
                    funding_rates = [rate['funding_rate'] * 100 for rate in rates]  # 转换为百分比
                    
                    fig.add_trace(go.Bar(
                        name=symbol,
                        x=exchanges,
                        y=funding_rates,
                        text=[f"{rate:.4f}%" for rate in funding_rates],
                        textposition='auto'
                    ))
            
            fig.update_layout(
                title="各交易所资金费率对比",
                xaxis_title="交易所",
                yaxis_title="资金费率 (%)",
                barmode='group',
                height=400
            )
            
            st.plotly_chart(fig, width='stretch', key="funding_rate_chart")
            
            # 策略说明
            with st.expander("💡 资金费率套利策略说明"):
                st.markdown("""
                **资金费率套利原理：**
                
                1. **正费率策略**：当永续合约资金费率为正时
                   - 在费率高的交易所做空永续合约
                   - 在现货市场买入等量资产
                   - 每8小时收取资金费率
                
                2. **负费率策略**：当永续合约资金费率为负时
                   - 在费率低的交易所做多永续合约
                   - 在现货市场卖出等量资产
                   - 每8小时支付较少的资金费率
                
                3. **风险控制**：
                   - 保持现货和永续合约的数量平衡
                   - 监控价格波动和强平风险
                   - 及时调整仓位以维持对冲
                
                **注意事项**：
                - 资金费率每8小时结算一次
                - 需要考虑交易手续费和滑点成本
                - 建议使用较大资金量以摊薄固定成本
                """)
        
        else:
            st.info(f"🔍 当前没有满足条件的资金费率套利机会（最小费率差异: {min_rate_diff}%）")
    
    else:
        st.info("📊 点击上方按钮获取最新的资金费率数据")

def show_orderbook_analysis():
    """显示订单簿深度与滑点分析"""
    from src.ui.analysis_components import render_orderbook_analysis
    render_orderbook_analysis(orderbook_analyzer)

def show_risk_dashboard():
    """显示动态风险仪表盘"""
    from src.ui.analysis_components import render_risk_dashboard
    render_risk_dashboard(risk_dashboard)

def show_transfer_path_planner():
    """显示转账路径规划器"""
    from src.ui.transfer_arbitrage_components import render_transfer_path_planner
    render_transfer_path_planner(transfer_path_planner)

def show_arbitrage_opportunities():
    """显示期现套利机会视图"""
    from src.ui.transfer_arbitrage_components import render_arbitrage_opportunities
    render_arbitrage_opportunities()

def show_exchange_health_monitor():
    """显示交易所健康状态监控功能"""
    from src.ui.monitoring_components import render_exchange_health_monitor
    render_exchange_health_monitor()

def show_cross_chain_analysis():
    """显示跨链转账效率与成本分析"""
    from src.ui.monitoring_components import render_cross_chain_analysis
    render_cross_chain_analysis()


def show_enhanced_ccxt_features():
    """显示增强的CCXT功能"""
    from src.ui.monitoring_components import render_enhanced_ccxt_features
    render_enhanced_ccxt_features()


def show_analytics_dashboard(engine: ArbitrageEngine, providers: List[BaseProvider]):
    """显示数据分析仪表盘"""
    from .ui.analytics_components import render_analytics_dashboard
    render_analytics_dashboard(engine, providers)


def show_professional_trading_interface(engine, providers):
    """显示专业交易界面"""
    from .ui.trading_components import render_professional_trading_interface
    render_professional_trading_interface(engine, providers)


def show_currency_comparison(engine, providers):
    """显示货币比对中心 - 使用分层架构"""
    from .ui.currency_hub import CurrencyHub, apply_currency_hub_styles
    
    # 应用样式
    apply_currency_hub_styles()
    
    # 初始化货币中心
    hub = CurrencyHub()
    
    # 渲染主界面
    hub.render_main_interface()

def show_system_settings(config):
    """显示系统设置页面"""
    from .ui.settings_components import render_system_settings
    render_system_settings(config)


def render_global_api_selector():
    """渲染全局API选择器"""
    st.sidebar.markdown("### 🌐 全局API设置")
    
    # 获取所有可用的免费API
    from src.providers.free_api import free_api_provider
    all_apis = free_api_provider.get_all_apis()
    
    # 初始化session state
    if 'global_selected_api' not in st.session_state:
        st.session_state.global_selected_api = 'coingecko'
    
    # API选择器
    selected_api = st.sidebar.selectbox(
        "选择全局API数据源",
        options=list(all_apis.keys()),
        index=list(all_apis.keys()).index(st.session_state.global_selected_api) if st.session_state.global_selected_api in all_apis else 0,
        format_func=lambda x: all_apis[x],
        key='global_selected_api',
        help="选择一个API作为全局数据源，所有页面都将使用此API获取数据。"
    )
    
    # 更新免费API提供者的配置
    selected_apis = [selected_api] if selected_api else []
    if selected_apis != free_api_provider.get_enabled_apis():
        free_api_provider.update_enabled_apis(selected_apis)
    
    # 显示当前选择的API状态
    api_status = "🟢 已连接" if selected_api else "🔴 未选择"
    st.sidebar.caption(f"状态: {api_status} | 当前: {all_apis.get(selected_api, '未选择')}")
    
    st.sidebar.markdown("---")


def main():
    """Main function to run the Streamlit application."""
    config = get_config()
    init_session_state(config)

    # 全局API选择器 - 放在侧边栏顶部
    render_global_api_selector()

    # 渲染导航栏
    render_navigation()
    
    # 渲染页面标题
    render_page_header(
        title="专业级套利分析平台",
        description="实时监控市场机会，智能分析套利策略，专业级风险管控",
        icon="🎯"
    )
    
    # 渲染快速统计
    render_quick_stats()
    
    # 主要功能区域
    st.markdown("## 🚀 快速访问")
    
    # 创建功能卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>🌍 货币概览</h3>
            <p>查看全球货币市场概况，实时价格和趋势分析</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入货币概览", key="goto_overview", use_container_width=True):
            st.switch_page("pages/1_world_currency_overview.py")
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>📈 详细分析</h3>
            <p>深入分析货币走势，技术指标和市场信号</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入详细分析", key="goto_analysis", use_container_width=True):
            st.switch_page("pages/2_chart_detailed_analysis.py")
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>⚖️ 货币比较</h3>
            <p>对比不同货币表现，发现投资机会</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入货币比较", key="goto_compare", use_container_width=True):
            st.switch_page("pages/3_balance_currency_comparison.py")

    # 第二行功能卡片
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>🔍 高级筛选</h3>
            <p>使用专业筛选工具，精准定位投资标的</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入高级筛选", key="goto_filter", use_container_width=True):
            st.switch_page("pages/4_search_advanced_filter.py")
    
    with col5:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: #333;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>📊 实时仪表盘</h3>
            <p>实时监控市场动态，智能预警系统</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入实时仪表盘", key="goto_dashboard", use_container_width=True):
            st.switch_page("pages/5_dashboard_realtime_dashboard.py")
    
    with col6:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            color: #333;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <h3>💼 专业交易</h3>
            <p>专业级交易界面，高级订单管理</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("进入专业交易", key="goto_trading", use_container_width=True):
            st.switch_page("pages/6_money_arbitrage_opportunities.py")

    # 监控组件区域
    st.markdown("---")
    st.markdown("## 📊 实时监控中心")
    
    # 创建监控组件标签页
    monitor_tab1, monitor_tab2, monitor_tab3, monitor_tab4 = st.tabs([
        "⚡ 执行监控", 
        "🛡️ 风险控制", 
        "🌐 网络监控",
        "📈 主控制台"
    ])
    
    with monitor_tab1:
        try:
            from components.execution_monitor import render_execution_monitor
            render_execution_monitor()
        except Exception as e:
            st.error(f"执行监控组件加载失败: {e}")
            st.info("正在开发中，敬请期待...")
    
    with monitor_tab2:
        try:
            from components.risk_assessment import render_risk_assessment
            render_risk_assessment()
        except Exception as e:
            st.error(f"风险控制组件加载失败: {e}")
            st.info("正在开发中，敬请期待...")
    
    with monitor_tab3:
        try:
            from components.network_monitor import render_network_monitor
            render_network_monitor()
        except Exception as e:
            st.error(f"网络监控组件加载失败: {e}")
            st.info("正在开发中，敬请期待...")
    
    with monitor_tab4:
        try:
            from components.main_console import render_main_console
            render_main_console()
        except Exception as e:
            st.error(f"主控制台组件加载失败: {e}")
            st.info("正在开发中，敬请期待...")

    # 如果用户点击了专业交易，显示原有的交易界面
    if st.session_state.get('show_trading', False):
        st.markdown("---")
        st.markdown("## 💼 专业交易界面")
        
        sidebar_controls()

        providers = get_providers(config, st.session_state)
        if not providers:
            st.error("没有可用的数据提供商。请在侧边栏中选择交易所或检查配置。")
            st.info("💡 提示：请在侧边栏中选择至少一个交易所来开始使用。")
            return

        engine = ArbitrageEngine(providers, config.get('arbitrage', {}))

        # 页面选择
        st.sidebar.markdown("---")
        page = st.sidebar.selectbox(
            "📊 选择功能",
            ["🏠 实时仪表盘", "💼 专业交易界面", "🌍 货币比对中心", "📈 数据分析中心", "🔍 新货币监控", "⚙️ 系统设置"],
            index=0
        )

        if page == "🏠 实时仪表盘":
            show_dashboard(engine, providers)
        elif page == "💼 专业交易界面":
            show_professional_trading_interface(engine, providers)
        elif page == "🌍 货币比对中心":
            show_currency_comparison(engine, providers)
        elif page == "📈 数据分析中心":
            show_analytics_dashboard(engine, providers)
        elif page == "🔍 新货币监控":
            from components.new_listing_monitor import render_new_listing_monitor
            render_new_listing_monitor()
        elif page == "⚙️ 系统设置":
            show_system_settings(config)

        # Auto refresh footer
        if st.session_state.get('auto_refresh_enabled', False):
            interval = st.session_state.get('auto_refresh_interval', 10)
            st.info(f"🔄 自动刷新已启用，每 {interval} 秒刷新一次")
            time.sleep(interval)
            st.rerun()
    
    # 渲染页面底部
    render_footer()

if __name__ == "__main__":
    main()
