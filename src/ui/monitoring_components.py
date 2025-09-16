"""
监控和跨链分析组件
包含交易所健康监控、跨链分析等功能组件
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import datetime
import asyncio
import time
from typing import Dict, List, Any

def render_exchange_health_monitor():
    """渲染交易所健康状态监控界面"""
    st.subheader("🏥 交易所健康状态监控")
    
    # 控制面板
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selected_exchanges = st.multiselect(
            "选择交易所",
            options=["binance", "okx", "bybit", "coinbase", "kraken", "huobi"],
            default=["binance", "okx", "bybit"],
            help="选择要监控的交易所"
        )
    
    with col2:
        check_interval = st.selectbox(
            "检查间隔",
            options=["实时", "1分钟", "5分钟", "15分钟"],
            index=1,
            help="健康检查的频率"
        )
    
    with col3:
        if st.button("🔄 刷新状态", type="primary"):
            st.rerun()
    
    if not selected_exchanges:
        st.warning("请至少选择一个交易所进行监控")
        return
    
    # 获取健康状态数据
    try:
        # 模拟健康状态数据
        health_data = _generate_mock_health_data(selected_exchanges)
        
        # 总体状态概览
        _render_health_overview(selected_exchanges, health_data)
        
        # 详细健康指标
        _render_health_metrics(selected_exchanges, health_data)
        
        # API延迟对比图表
        _render_latency_comparison(selected_exchanges, health_data)
        
        # 健康状态历史趋势
        _render_health_trends(selected_exchanges, health_data)
        
        # 警报设置
        _render_alert_settings(selected_exchanges, health_data)
        
        # 功能说明
        _render_health_monitor_help()
    
    except Exception as e:
        st.error(f"获取交易所健康数据时出错: {str(e)}")
        st.info("请检查网络连接和API配置")

def render_cross_chain_analysis():
    """渲染跨链转账效率与成本分析界面"""
    st.subheader("🌉 跨链转账效率与成本分析")
    
    # 控制面板
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 源网络选择
        from_networks = ["Ethereum", "BSC", "Polygon", "Arbitrum", "Optimism", "Avalanche"]
        from_network = st.selectbox(
            "源网络",
            from_networks,
            key="cross_chain_from_network"
        )
    
    with col2:
        # 目标网络选择
        to_networks = [net for net in from_networks if net != from_network]
        to_network = st.selectbox(
            "目标网络",
            to_networks,
            key="cross_chain_to_network"
        )
    
    with col3:
        # 代币选择
        tokens = ["USDT", "USDC", "ETH", "BTC", "BNB"]
        token = st.selectbox(
            "代币",
            tokens,
            key="cross_chain_token"
        )
    
    with col4:
        # 转账金额
        amount = st.number_input(
            "转账金额",
            min_value=1.0,
            max_value=1000000.0,
            value=1000.0,
            step=100.0,
            key="cross_chain_amount"
        )
    
    # 分析按钮
    if st.button("🔍 分析跨链路由", key="analyze_cross_chain"):
        with st.spinner("正在分析跨链转账路由..."):
            try:
                # 生成模拟分析数据
                analysis = _generate_mock_cross_chain_analysis(from_network, to_network, token, amount)
                
                if analysis.get('routes'):
                    st.success(f"找到 {analysis['total_routes']} 条可用路由")
                    
                    # 最佳路由推荐
                    _render_best_routes(analysis)
                    
                    # 详细路由对比表
                    _render_route_comparison(analysis)
                    
                    # 成本分析图表
                    _render_cost_analysis_charts(analysis)
                    
                    # 成本构成分析
                    _render_cost_breakdown(analysis)
                    
                    # 统计信息
                    _render_cross_chain_statistics(analysis)
                
                else:
                    st.error(analysis.get('error', '分析失败'))
            
            except Exception as e:
                st.error(f"分析过程中发生错误: {str(e)}")
    
    # 功能说明
    _render_cross_chain_help()

def render_enhanced_ccxt_features():
    """渲染增强的CCXT功能界面"""
    st.header("🚀 增强CCXT交易所支持")
    
    # 支持的交易所信息
    _render_supported_exchanges()
    
    # 实时价格对比
    _render_price_comparison()
    
    # 套利机会分析
    _render_arbitrage_analysis()

# 辅助函数
def _generate_mock_health_data(exchanges: List[str]) -> Dict[str, Any]:
    """生成模拟健康状态数据"""
    health_data = {}
    for exchange in exchanges:
        health_data[exchange] = {
            'overall_status': np.random.choice(['healthy', 'warning', 'error'], p=[0.7, 0.2, 0.1]),
            'api_status': np.random.choice([True, False], p=[0.9, 0.1]),
            'time_sync': np.random.choice([True, False], p=[0.95, 0.05]),
            'api_latency': np.random.normal(150, 50),
            'trading_pairs_count': np.random.randint(100, 500),
            'volume_24h': np.random.uniform(1000000, 10000000),
            'orderbook_depth': f"{np.random.randint(50, 200)}层",
            'last_update': datetime.datetime.now().strftime("%H:%M:%S")
        }
    return health_data

def _render_health_overview(exchanges: List[str], health_data: Dict[str, Any]):
    """渲染健康状态概览"""
    st.markdown("### 📊 总体状态概览")
    
    status_cols = st.columns(len(exchanges))
    for i, exchange in enumerate(exchanges):
        with status_cols[i]:
            if exchange in health_data:
                data = health_data[exchange]
                overall_status = data.get('overall_status', 'unknown')
                
                if overall_status == 'healthy':
                    st.success(f"✅ {exchange.upper()}")
                    st.metric("状态", "健康")
                elif overall_status == 'warning':
                    st.warning(f"⚠️ {exchange.upper()}")
                    st.metric("状态", "警告")
                else:
                    st.error(f"❌ {exchange.upper()}")
                    st.metric("状态", "异常")
                
                # 显示响应时间
                if 'api_latency' in data:
                    st.metric("API延迟", f"{data['api_latency']:.0f}ms")
            else:
                st.error(f"❌ {exchange.upper()}")
                st.metric("状态", "连接失败")

def _render_health_metrics(exchanges: List[str], health_data: Dict[str, Any]):
    """渲染详细健康指标"""
    st.markdown("### 📈 详细健康指标")
    
    # 创建健康指标表格
    health_metrics = []
    for exchange in exchanges:
        if exchange in health_data:
            data = health_data[exchange]
            metrics = {
                "交易所": exchange.upper(),
                "API状态": "✅ 正常" if data.get('api_status') else "❌ 异常",
                "时间同步": "✅ 同步" if data.get('time_sync') else "❌ 不同步",
                "API延迟(ms)": f"{data.get('api_latency', 0):.0f}",
                "交易对数量": data.get('trading_pairs_count', 0),
                "24h交易量": f"${data.get('volume_24h', 0):,.0f}",
                "订单簿深度": data.get('orderbook_depth', 'N/A'),
                "最后更新": data.get('last_update', 'N/A')
            }
            health_metrics.append(metrics)
        else:
            metrics = {
                "交易所": exchange.upper(),
                "API状态": "❌ 连接失败",
                "时间同步": "❌ 无法检测",
                "API延迟(ms)": "N/A",
                "交易对数量": "N/A",
                "24h交易量": "N/A",
                "订单簿深度": "N/A",
                "最后更新": "N/A"
            }
            health_metrics.append(metrics)
    
    if health_metrics:
        df_health = pd.DataFrame(health_metrics)
        st.dataframe(df_health, use_container_width=True)

def _render_latency_comparison(exchanges: List[str], health_data: Dict[str, Any]):
    """渲染API延迟对比图表"""
    st.markdown("### ⚡ API延迟对比")
    
    latency_data = []
    for exchange in exchanges:
        if exchange in health_data and 'api_latency' in health_data[exchange]:
            latency_data.append({
                "交易所": exchange.upper(),
                "延迟(ms)": health_data[exchange]['api_latency']
            })
    
    if latency_data:
        df_latency = pd.DataFrame(latency_data)
        
        fig_latency = px.bar(
            df_latency,
            x="交易所",
            y="延迟(ms)",
            title="交易所API延迟对比",
            color="延迟(ms)",
            color_continuous_scale="RdYlGn_r"
        )
        fig_latency.update_layout(
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_latency, use_container_width=True, key="exchange_latency_chart")

def _render_health_trends(exchanges: List[str], health_data: Dict[str, Any]):
    """渲染健康状态历史趋势"""
    st.markdown("### 📊 健康状态趋势")
    
    # 生成模拟的历史数据
    dates = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(hours=24),
        end=datetime.datetime.now(),
        freq='H'
    )
    
    trend_data = []
    for exchange in exchanges[:3]:  # 限制显示前3个交易所
        if exchange in health_data:
            base_latency = health_data[exchange].get('api_latency', 100)
            # 生成带有随机波动的延迟数据
            latencies = base_latency + np.random.normal(0, 20, len(dates))
            latencies = np.maximum(latencies, 10)  # 确保延迟不为负数
            
            for date, latency in zip(dates, latencies):
                trend_data.append({
                    "时间": date,
                    "交易所": exchange.upper(),
                    "API延迟(ms)": latency
                })
    
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        
        fig_trend = px.line(
            df_trend,
            x="时间",
            y="API延迟(ms)",
            color="交易所",
            title="24小时API延迟趋势"
        )
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, use_container_width=True, key="api_latency_trend_chart")

def _render_alert_settings(exchanges: List[str], health_data: Dict[str, Any]):
    """渲染警报设置"""
    st.markdown("### 🚨 警报设置")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        latency_threshold = st.number_input(
            "API延迟阈值 (ms)",
            min_value=50,
            max_value=5000,
            value=1000,
            step=50,
            help="超过此延迟将触发警报"
        )
    
    with col2:
        downtime_threshold = st.number_input(
            "停机时间阈值 (分钟)",
            min_value=1,
            max_value=60,
            value=5,
            step=1,
            help="连续停机超过此时间将触发警报"
        )
    
    with col3:
        enable_notifications = st.checkbox(
            "启用通知",
            value=True,
            help="启用邮件/短信通知"
        )
    
    # 检查是否有警报
    alerts = []
    for exchange in exchanges:
        if exchange in health_data:
            data = health_data[exchange]
            if data.get('api_latency', 0) > latency_threshold:
                alerts.append(f"⚠️ {exchange.upper()}: API延迟过高 ({data['api_latency']:.0f}ms)")
            if not data.get('api_status'):
                alerts.append(f"🚨 {exchange.upper()}: API连接失败")
            if not data.get('time_sync'):
                alerts.append(f"⚠️ {exchange.upper()}: 时间同步异常")
    
    if alerts:
        st.markdown("### 🚨 当前警报")
        for alert in alerts:
            st.error(alert)
    else:
        st.success("✅ 所有监控的交易所状态正常")

def _render_health_monitor_help():
    """渲染健康监控功能说明"""
    with st.expander("ℹ️ 功能说明"):
        st.markdown("""
        **交易所健康状态监控功能包括：**
        
        📊 **实时监控指标：**
        - API连接状态和响应时间
        - 服务器时间同步状态
        - 交易对数量和24小时交易量
        - 订单簿深度和流动性
        
        📈 **数据分析：**
        - API延迟对比和趋势分析
        - 健康状态历史记录
        - 异常检测和预警
        
        🚨 **智能警报：**
        - 自定义延迟和停机阈值
        - 实时通知和警报推送
        - 多渠道通知支持
        
        💡 **使用建议：**
        - 定期检查交易所健康状态
        - 根据延迟情况选择最优交易所
        - 设置合理的警报阈值
        - 关注异常模式和趋势变化
        """)

def _generate_mock_cross_chain_analysis(from_network: str, to_network: str, token: str, amount: float) -> Dict[str, Any]:
    """生成模拟跨链分析数据"""
    bridges = ["Stargate", "Multichain", "cBridge", "Hop", "Synapse"]
    routes = []
    
    for bridge in bridges:
        bridge_fee = np.random.uniform(0.1, 2.0) * amount / 100
        gas_cost = np.random.uniform(5, 50)
        total_cost = bridge_fee + gas_cost
        estimated_time = np.random.randint(300, 3600)  # 5分钟到1小时
        
        route = {
            'bridge': bridge,
            'bridge_fee': bridge_fee,
            'gas_cost': gas_cost,
            'total_cost': total_cost,
            'fee_rate': total_cost / amount,
            'cost_percentage': (total_cost / amount) * 100,
            'estimated_time': estimated_time
        }
        routes.append(route)
    
    # 排序找出最佳路由
    best_cost_route = min(routes, key=lambda x: x['total_cost'])
    fastest_route = min(routes, key=lambda x: x['estimated_time'])
    
    # 统计信息
    costs = [r['total_cost'] for r in routes]
    times = [r['estimated_time'] for r in routes]
    
    statistics = {
        'min_cost': min(costs),
        'max_cost': max(costs),
        'avg_cost': np.mean(costs),
        'min_time': min(times),
        'max_time': max(times),
        'avg_time': np.mean(times)
    }
    
    return {
        'routes': routes,
        'total_routes': len(routes),
        'best_cost_route': best_cost_route,
        'fastest_route': fastest_route,
        'statistics': statistics
    }

def _render_best_routes(analysis: Dict[str, Any]):
    """渲染最佳路由推荐"""
    st.subheader("💡 最佳路由推荐")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💰 最低成本路由**")
        best_cost = analysis['best_cost_route']
        st.info(f"""
        **桥**: {best_cost['bridge']}
        **总成本**: ${best_cost['total_cost']:.4f}
        **成本占比**: {best_cost['cost_percentage']:.3f}%
        **预计时间**: {best_cost['estimated_time']//60}分钟
        """)
    
    with col2:
        st.markdown("**⚡ 最快路由**")
        fastest = analysis['fastest_route']
        st.info(f"""
        **桥**: {fastest['bridge']}
        **总成本**: ${fastest['total_cost']:.4f}
        **成本占比**: {fastest['cost_percentage']:.3f}%
        **预计时间**: {fastest['estimated_time']//60}分钟
        """)

def _render_route_comparison(analysis: Dict[str, Any]):
    """渲染详细路由对比表"""
    st.subheader("📊 路由详细对比")
    
    route_data = []
    for route in analysis['routes']:
        route_data.append({
            '跨链桥': route['bridge'],
            '总成本 ($)': f"{route['total_cost']:.4f}",
            '桥费用 ($)': f"{route['bridge_fee']:.4f}",
            'Gas费用 ($)': f"{route['gas_cost']:.4f}",
            '费率 (%)': f"{route['fee_rate']*100:.3f}",
            '成本占比 (%)': f"{route['cost_percentage']:.3f}",
            '预计时间 (分钟)': f"{route['estimated_time']//60}",
            '评级': '⭐⭐⭐' if route == analysis['best_cost_route'] else 
                   '⭐⭐' if route == analysis['fastest_route'] else '⭐'
        })
    
    df_routes = pd.DataFrame(route_data)
    st.dataframe(df_routes, use_container_width=True)

def _render_cost_analysis_charts(analysis: Dict[str, Any]):
    """渲染成本分析图表"""
    st.subheader("📈 成本分析可视化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 成本对比柱状图
        fig_cost = px.bar(
            x=[route['bridge'] for route in analysis['routes']],
            y=[route['total_cost'] for route in analysis['routes']],
            title="各桥总成本对比",
            labels={'x': '跨链桥', 'y': '总成本 ($)'},
            color=[route['total_cost'] for route in analysis['routes']],
            color_continuous_scale='RdYlGn_r'
        )
        fig_cost.update_layout(height=400)
        st.plotly_chart(fig_cost, use_container_width=True, key="bridge_cost_comparison")
    
    with col2:
        # 时间对比柱状图
        fig_time = px.bar(
            x=[route['bridge'] for route in analysis['routes']],
            y=[route['estimated_time']//60 for route in analysis['routes']],
            title="各桥预计时间对比",
            labels={'x': '跨链桥', 'y': '预计时间 (分钟)'},
            color=[route['estimated_time'] for route in analysis['routes']],
            color_continuous_scale='RdYlBu_r'
        )
        fig_time.update_layout(height=400)
        st.plotly_chart(fig_time, use_container_width=True, key="bridge_time_comparison")

def _render_cost_breakdown(analysis: Dict[str, Any]):
    """渲染成本构成分析"""
    st.subheader("🔍 成本构成分析")
    
    # 选择一个路由进行详细分析
    selected_bridge = st.selectbox(
        "选择桥进行详细分析",
        [route['bridge'] for route in analysis['routes']],
        key="selected_bridge_analysis"
    )
    
    selected_route = next(route for route in analysis['routes'] if route['bridge'] == selected_bridge)
    
    # 饼图显示成本构成
    cost_breakdown = {
        '桥费用': selected_route['bridge_fee'],
        'Gas费用': selected_route['gas_cost']
    }
    
    fig_pie = px.pie(
        values=list(cost_breakdown.values()),
        names=list(cost_breakdown.keys()),
        title=f"{selected_bridge} 成本构成"
    )
    st.plotly_chart(fig_pie, use_container_width=True, key="bridge_cost_breakdown")

def _render_cross_chain_statistics(analysis: Dict[str, Any]):
    """渲染跨链统计信息"""
    st.subheader("📊 统计信息")
    
    stats = analysis['statistics']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "最低成本",
            f"${stats['min_cost']:.4f}",
            f"{((stats['min_cost']/stats['max_cost']-1)*100):+.1f}%"
        )
    
    with col2:
        st.metric(
            "平均成本",
            f"${stats['avg_cost']:.4f}",
            f"{((stats['avg_cost']/stats['max_cost']-1)*100):+.1f}%"
        )
    
    with col3:
        st.metric(
            "最快时间",
            f"{stats['min_time']//60}分钟",
            f"{((stats['min_time']/stats['max_time']-1)*100):+.1f}%"
        )
    
    with col4:
        st.metric(
            "平均时间",
            f"{stats['avg_time']//60}分钟",
            f"{((stats['avg_time']/stats['max_time']-1)*100):+.1f}%"
        )

def _render_cross_chain_help():
    """渲染跨链分析功能说明"""
    with st.expander("ℹ️ 功能说明", expanded=False):
        st.markdown("""
        ### 跨链转账效率与成本分析
        
        **主要功能:**
        - 🔍 **多桥对比**: 同时分析多个跨链桥的报价和性能
        - 💰 **成本分析**: 详细分解桥费用、Gas费用等成本构成
        - ⚡ **效率评估**: 比较不同桥的转账速度和确认时间
        - 📊 **可视化**: 直观展示成本和时间对比
        - 💡 **智能推荐**: 根据成本和速度推荐最佳路由
        
        **支持的跨链桥:**
        - Stargate Finance
        - Multichain (Anyswap)
        - Celer cBridge
        - Hop Protocol
        - Synapse Protocol
        
        **支持的网络:**
        - Ethereum
        - BSC (Binance Smart Chain)
        - Polygon
        - Arbitrum
        - Optimism
        - Avalanche
        
        **注意事项:**
        - 费用估算基于当前Gas价格，实际费用可能有所不同
        - 转账时间为预估值，实际时间受网络拥堵影响
        - 建议在实际转账前再次确认最新报价
        """)

def _render_supported_exchanges():
    """渲染支持的交易所信息"""
    with st.expander("📋 支持的免费交易所", expanded=True):
        exchanges = [
            {'name': 'Binance', 'id': 'binance', 'status': 'active', 'rate_limit': 1200},
            {'name': 'OKX', 'id': 'okx', 'status': 'active', 'rate_limit': 600},
            {'name': 'Bybit', 'id': 'bybit', 'status': 'active', 'rate_limit': 600},
            {'name': 'Coinbase', 'id': 'coinbase', 'status': 'active', 'rate_limit': 300},
            {'name': 'Kraken', 'id': 'kraken', 'status': 'active', 'rate_limit': 300}
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("活跃交易所")
            active_exchanges = [ex for ex in exchanges if ex['status'] == 'active']
            if active_exchanges:
                for ex in active_exchanges:
                    st.success(f"✅ {ex['name']} ({ex['id']})")
                    st.caption(f"限制: {ex['rate_limit']}/分钟")
            else:
                st.warning("暂无活跃交易所")
        
        with col2:
            st.subheader("支持的交易对")
            symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
            for symbol in symbols:
                st.info(f"📈 {symbol}")

def _render_price_comparison():
    """渲染实时价格对比"""
    st.subheader("💰 多交易所实时价格对比")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        selected_symbol = st.selectbox(
            "选择交易对",
            options=["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"],
            key="ccxt_symbol_select"
        )
    
    with col2:
        if st.button("🔄 刷新价格", key="refresh_ccxt_prices"):
            st.session_state.ccxt_refresh_trigger = time.time()
    
    with col3:
        auto_refresh = st.checkbox("自动刷新", key="ccxt_auto_refresh")
    
    # 获取价格数据
    if st.button("获取价格数据", key="get_ccxt_prices") or 'ccxt_refresh_trigger' in st.session_state:
        with st.spinner(f"正在获取 {selected_symbol} 的价格数据..."):
            try:
                # 生成模拟价格数据
                exchanges = ["BINANCE", "OKX", "BYBIT", "COINBASE", "KRAKEN"]
                base_price = np.random.uniform(30000, 70000) if "BTC" in selected_symbol else np.random.uniform(2000, 4000)
                
                tickers = []
                for exchange in exchanges:
                    price_variation = np.random.uniform(-0.02, 0.02)
                    price = base_price * (1 + price_variation)
                    
                    ticker = {
                        'exchange': exchange.lower(),
                        'price': price,
                        'bid': price * 0.999,
                        'ask': price * 1.001,
                        'change_24h': np.random.uniform(-5, 5),
                        'volume': np.random.uniform(1000, 10000),
                        'datetime': datetime.datetime.now().isoformat()
                    }
                    tickers.append(ticker)
                
                if tickers:
                    # 创建价格对比表
                    df_data = []
                    for ticker in tickers:
                        df_data.append({
                            '交易所': ticker['exchange'].upper(),
                            '最新价格': f"${ticker['price']:.4f}" if ticker['price'] else "N/A",
                            '买入价': f"${ticker['bid']:.4f}" if ticker['bid'] else "N/A",
                            '卖出价': f"${ticker['ask']:.4f}" if ticker['ask'] else "N/A",
                            '24h变化': f"{ticker['涨跌24h']:.2f}%" if ticker['涨跌24h'] else "N/A",
                            '成交量': f"{ticker['volume']:.2f}" if ticker['volume'] else "N/A",
                            '更新时间': ticker['datetime'][:19] if ticker['datetime'] else "N/A"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # 价格分析
                    prices = [t['price'] for t in tickers if t['price']]
                    if len(prices) >= 2:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("平均价格", f"${np.mean(prices):.4f}")
                        
                        with col2:
                            st.metric("最高价格", f"${max(prices):.4f}")
                        
                        with col3:
                            st.metric("最低价格", f"${min(prices):.4f}")
                        
                        with col4:
                            spread_pct = ((max(prices) - min(prices)) / min(prices)) * 100
                            st.metric("价差", f"{spread_pct:.2f}%")
                        
                        # 价格分布图
                        fig = px.bar(
                            x=[t['exchange'].upper() for t in tickers if t['price']],
                            y=prices,
                            title=f"{selected_symbol} 各交易所价格对比",
                            labels={'x': '交易所', 'y': '价格 (USD)'}
                        )
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True, key="exchange_price_comparison")
                else:
                    st.warning("未获取到价格数据")
                    
            except Exception as e:
                st.error(f"获取数据时出错: {str(e)}")

def _render_arbitrage_analysis():
    """渲染套利机会分析"""
    st.subheader("🎯 实时套利机会")
    
    if st.button("分析套利机会", key="analyze_arbitrage"):
        with st.spinner("正在分析套利机会..."):
            try:
                # 生成模拟套利机会
                opportunities = []
                exchanges = ["binance", "okx", "bybit", "coinbase", "kraken"]
                
                for i in range(5):
                    buy_exchange = np.random.choice(exchanges)
                    sell_exchange = np.random.choice([ex for ex in exchanges if ex != buy_exchange])
                    
                    buy_price = np.random.uniform(30000, 35000)
                    profit_pct = np.random.uniform(0.1, 2.0)
                    sell_price = buy_price * (1 + profit_pct / 100)
                    profit_abs = sell_price - buy_price
                    
                    opportunity = {
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_pct': profit_pct,
                        'profit_abs': profit_abs
                    }
                    opportunities.append(opportunity)
                
                # 按收益率排序
                opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
                
                if opportunities:
                    st.success(f"发现 {len(opportunities)} 个套利机会！")
                    
                    # 显示前5个最佳机会
                    top_opportunities = opportunities[:5]
                    
                    for i, opp in enumerate(top_opportunities, 1):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                            
                            with col1:
                                st.write(f"**#{i}**")
                            
                            with col2:
                                st.write(f"**买入:** {opp['buy_exchange'].upper()}")
                                st.write(f"价格: ${opp['buy_price']:.4f}")
                            
                            with col3:
                                st.write(f"**卖出:** {opp['sell_exchange'].upper()}")
                                st.write(f"价格: ${opp['sell_price']:.4f}")
                            
                            with col4:
                                profit_color = "green" if opp['profit_pct'] > 0.5 else "orange"
                                st.markdown(f"<span style='color:{profit_color}'>**+{opp['profit_pct']:.2f}%**</span>", unsafe_allow_html=True)
                                st.write(f"${opp['profit_abs']:.4f}")
                            
                            st.divider()
                    
                    # 套利机会图表
                    if len(opportunities) > 1:
                        fig_arb = px.scatter(
                            x=[f"{opp['buy_exchange']}->{opp['sell_exchange']}" for opp in opportunities],
                            y=[opp['profit_pct'] for opp in opportunities],
                            title="套利机会收益率分布",
                            labels={'x': '交易路径', 'y': '收益率 (%)'},
                            color=[opp['profit_pct'] for opp in opportunities],
                            color_continuous_scale='RdYlGn'
                        )
                        fig_arb.update_layout(height=400)
                        st.plotly_chart(fig_arb, use_container_width=True, key="arbitrage_opportunities_chart")
                else:
                    st.warning("当前没有发现套利机会")
                    
            except Exception as e:
                st.error(f"分析套利机会时出错: {str(e)}")