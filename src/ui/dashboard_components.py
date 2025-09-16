"""
仪表盘组件模块 - 拆分app.py中的长函数为可重用组件
"""

import streamlit as st
import pandas as pd
import asyncio
from typing import List, Dict, Any
from ..providers.base import BaseProvider
from ..providers.cex import CEXProvider
from ..providers.free_api import free_api_provider


def render_cex_price_comparison(providers: List[BaseProvider], price_placeholder):
    """渲染CEX价格对比组件"""
    with st.spinner("正在获取CEX交易所最新价格..."):
        tasks = []
        provider_symbol_pairs = []
        cex_providers = [p for p in providers if isinstance(p, CEXProvider)]
        symbols = st.session_state.get('selected_symbols', [])

        if not cex_providers:
            price_placeholder.warning("请在侧边栏选择至少一个CEX交易所。")
            return
        
        if not symbols:
            price_placeholder.warning("请在侧边栏选择至少一个交易对。")
            return

        for symbol in symbols:
            for provider in cex_providers:
                tasks.append(provider.get_ticker(symbol))
                provider_symbol_pairs.append((provider.name, symbol))

        from ..app import safe_run_async
        all_tickers = safe_run_async(asyncio.gather(*tasks, return_exceptions=True))

        processed_tickers = [
            {'symbol': t['symbol'], 'provider': provider_symbol_pairs[i][0], 'price': t['last']}
            for i, t in enumerate(all_tickers) if isinstance(t, dict) and t.get('last') is not None
        ]

        if processed_tickers:
            price_df = pd.DataFrame(processed_tickers)
            pivot_df = price_df.pivot(index='symbol', columns='provider', values='price')
            price_placeholder.dataframe(pivot_df.style.format("{:.4f}"), use_container_width=True)
        else:
            price_placeholder.warning("未能获取任何有效的CEX价格数据。")


def render_free_api_comparison():
    """渲染免费API价格对比组件"""
    st.info("💡 **功能说明**: 实时比较 Binance、OKX、Bybit、Coinbase、Kraken、Huobi、KuCoin、Gate.io 等8个主要交易所的货币价格。")
    
    free_api_col1, free_api_col2 = st.columns([3, 1])

    with free_api_col2:
        selected_symbols_free = _render_symbol_selector()

    with free_api_col1:
        if not selected_symbols_free:
            st.info("请在右侧选择至少一个交易对进行查询。")
        else:
            _render_free_api_data(selected_symbols_free)


def _render_symbol_selector():
    """渲染交易对选择器"""
    st.markdown("**交易对选择**")
    all_symbols = free_api_provider.get_popular_symbols()
    search_term = st.text_input("🔍 搜索货币对", "", key="symbol_search_free")

    if search_term:
        filtered_symbols = [s for s in all_symbols if search_term.upper() in s.upper()]
    else:
        filtered_symbols = all_symbols

    return st.multiselect(
        "选择交易对",
        options=filtered_symbols,
        default=[s for s in ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'] if s in filtered_symbols],
        key="selected_symbols_free"
    )


def _render_free_api_data(selected_symbols_free):
    """渲染免费API数据"""
    with st.spinner("获取免费API价格数据..."):
        async def fetch_free_data():
            # 使用全局API设置
            enabled_apis = free_api_provider.get_enabled_apis()
            selected_api = enabled_apis[0] if enabled_apis else 'coingecko'
            return await free_api_provider.get_exchange_prices_from_api(selected_symbols_free, selected_api)

        from ..app import safe_run_async
        free_data = safe_run_async(fetch_free_data())

        if not free_data:
            st.warning("未能获取任何数据。请检查API或稍后再试。")
            return

        for symbol, price_list in free_data.items():
            if not price_list:
                st.write(f"### {symbol} - 未找到数据")
                continue

            _render_symbol_price_comparison(symbol, price_list)


def _render_symbol_price_comparison(symbol: str, price_list: List[Dict]):
    """渲染单个交易对的价格对比"""
    st.markdown(f"### 💰 {symbol} 价格对比")
    df_comparison = pd.DataFrame(price_list)
    
    prices = df_comparison['price_usd'].dropna()
    if not prices.empty:
        max_price, min_price = prices.max(), prices.min()
        avg_price = prices.mean()
        spread_pct = ((max_price - min_price) / min_price * 100) if min_price > 0 else 0
        
        stat_cols = st.columns(4)
        stat_cols[0].metric("最高价", f"${max_price:,.6f}")
        stat_cols[1].metric("最低价", f"${min_price:,.6f}")
        stat_cols[2].metric("平均价", f"${avg_price:,.6f}")
        stat_cols[3].metric("价差", f"{spread_pct:.3f}%", 
                           "🟢" if spread_pct > 1 else "🟡" if spread_pct > 0.3 else "🔴")
    
    st.dataframe(
        df_comparison.drop(columns=['timestamp']),
        use_container_width=True,
        hide_index=True,
        column_config={
            'exchange': st.column_config.TextColumn("交易所"),
            'price_usd': st.column_config.NumberColumn("价格 (USD)", format="$%.6f"),
            'change_24h': st.column_config.NumberColumn("24h变化%", format="%.2f%%"),
            'volume_24h': st.column_config.NumberColumn("24h成交量", format="$%d"),
        }
    )
    st.markdown("---")


def render_risk_monitoring_panel():
    """渲染实时风险监控面板"""
    st.subheader("🚨 实时风险监控")
    
    risk_monitor_col1, risk_monitor_col2 = st.columns([2, 1])
    
    with risk_monitor_col1:
        _render_risk_metrics_table()
    
    with risk_monitor_col2:
        _render_risk_alerts_and_controls()


def _render_risk_metrics_table():
    """渲染风险指标表格"""
    risk_metrics = [
        {"指标": "总资金", "当前值": "$98,750", "阈值": "$100,000", "状态": "🟡 关注", "变化": "-1.25%"},
        {"指标": "日盈亏", "当前值": "+$1,250", "阈值": "-$20,000", "状态": "🟢 正常", "变化": "+1.27%"},
        {"指标": "最大回撤", "当前值": "-3.2%", "阈值": "-15.0%", "状态": "🟢 安全", "变化": "+0.8%"},
        {"指标": "持仓风险", "当前值": "2/5", "阈值": "5/5", "状态": "🟢 正常", "变化": "0"},
        {"指标": "相关性", "当前值": "0.65", "阈值": "0.70", "状态": "🟡 关注", "变化": "+0.05"}
    ]
    
    df_risk = pd.DataFrame(risk_metrics)
    st.dataframe(df_risk, width='stretch', hide_index=True)


def _render_risk_alerts_and_controls():
    """渲染风险警报和控制按钮"""
    st.markdown("**🔔 风险警报**")
    
    alerts = [
        "🟡 BTC/USDT 相关性过高 (0.85)",
        "🟢 ETH/USDT 套利机会出现",
        "🔴 总资金接近止损线"
    ]
    
    for alert in alerts:
        st.write(alert)
    
    st.markdown("**⚡ 紧急操作**")
    if st.button("🛑 紧急止损", key="emergency_stop", help="立即关闭所有持仓"):
        st.error("🚨 紧急止损已触发")
    
    if st.button("⏸️ 暂停交易", key="pause_trading", help="暂停所有新交易"):
        st.warning("⚠️ 交易已暂停")
    
    if st.button("🔄 重置风险", key="reset_risk", help="重置风险参数"):
        st.info("ℹ️ 风险参数已重置")


def render_batch_monitoring_panel():
    """渲染批量监控管理面板"""
    st.subheader("📋 批量监控管理")
    
    monitor_col1, monitor_col2 = st.columns([4, 1])
    
    with monitor_col1:
        _render_monitor_list()
    
    with monitor_col2:
        _render_monitor_controls()


def _render_monitor_list():
    """渲染监控列表"""
    st.markdown("**活跃监控列表**")
    
    monitor_data = [
        {"交易对": "BTC/USDT", "状态": "🟢 监控中", "触发条件": ">1.5%", "当前价差": "1.25%", "操作": "暂停"},
        {"交易对": "ETH/USDT", "状态": "🟡 等待中", "触发条件": ">1.0%", "当前价差": "0.89%", "操作": "修改"},
        {"交易对": "ADA/USDT", "状态": "🔴 已暂停", "触发条件": ">2.0%", "当前价差": "2.15%", "操作": "启动"}
    ]
    
    for i, item in enumerate(monitor_data):
        with st.container():
            item_col1, item_col2, item_col3, item_col4, item_col5 = st.columns([3, 1, 1, 1, 1])
            
            with item_col1:
                st.write(f"**{item['交易对']}** - {item['状态']}")
            with item_col2:
                st.write(f"触发: {item['触发条件']}")
            with item_col3:
                st.write(f"当前: {item['当前价差']}")
            with item_col4:
                if st.button(item['操作'], key=f"monitor_action_{i}"):
                    st.success(f"{item['操作']}操作已执行")
            with item_col5:
                if st.button("删除", key=f"monitor_delete_{i}"):
                    st.warning(f"已删除 {item['交易对']} 监控")


def _render_monitor_controls():
    """渲染监控控制面板"""
    st.markdown("**添加新监控**")
    new_symbol = st.text_input("交易对", placeholder="BTC/USDT", key="new_monitor_symbol")
    new_threshold = st.number_input("触发阈值 (%)", min_value=0.1, max_value=10.0, value=1.0, step=0.1, key="new_threshold")
    
    if st.button("➕ 添加监控", key="add_monitor"):
        if new_symbol:
            st.success(f"已添加 {new_symbol} 监控 (>{new_threshold}%)")
        else:
            st.error("请输入交易对")
    
    st.markdown("**批量操作**")
    if st.button("▶️ 全部启动", key="start_all_monitors"):
        st.success("所有监控已启动")
    if st.button("⏸️ 全部暂停", key="pause_all_monitors"):
        st.warning("所有监控已暂停")
    if st.button("🗑️ 清空列表", key="clear_all_monitors"):
        st.error("监控列表已清空")