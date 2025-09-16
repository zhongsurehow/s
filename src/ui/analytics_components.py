"""
数据分析组件模块
包含数据分析仪表盘的所有渲染函数
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from ..core.analytics import analytics_engine, PerformanceMetrics, BacktestResult
from ..core.market_depth import market_depth_analyzer


def render_analytics_dashboard(engine, providers: List):
    """渲染数据分析仪表盘"""
    st.title("📈 数据分析中心")
    st.markdown("---")
    
    # 初始化分析引擎
    if 'analytics_engine' not in st.session_state:
        st.session_state.analytics_engine = analytics_engine
    
    analytics = st.session_state.analytics_engine
    
    # 分析选项卡
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 收益分析", 
        "🔄 历史回测", 
        "⚡ 策略优化", 
        "📈 市场分析"
    ])
    
    with tab1:
        _render_profit_analysis()
    
    with tab2:
        _render_backtest_analysis()
    
    with tab3:
        _render_strategy_optimization()
    
    with tab4:
        _render_market_analysis()


def _render_profit_analysis():
    """渲染收益分析标签页"""
    st.subheader("💰 收益分析")
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now())
    
    # 生成模拟收益数据
    if st.button("🔄 生成收益报告", key="generate_profit_report"):
        with st.spinner("正在分析收益数据..."):
            time.sleep(1)  # 模拟计算时间
            
            # 模拟收益指标
            metrics = PerformanceMetrics(
                total_return=0.156,
                sharpe_ratio=2.34,
                max_drawdown=0.045,
                win_rate=0.78,
                profit_factor=3.2,
                avg_trade_return=0.0023,
                total_trades=1247,
                profitable_trades=973
            )
            
            # 显示关键指标
            _display_performance_metrics(metrics)
            
            # 收益曲线图
            _render_cumulative_returns_chart(start_date, end_date)


def _display_performance_metrics(metrics: PerformanceMetrics):
    """显示关键指标"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "总收益率",
            f"{metrics.total_return:.2%}",
            f"+{metrics.total_return*100:.1f}%"
        )
    
    with col2:
        st.metric(
            "夏普比率",
            f"{metrics.sharpe_ratio:.2f}",
            "优秀" if metrics.sharpe_ratio > 2 else "良好"
        )
    
    with col3:
        st.metric(
            "最大回撤",
            f"{metrics.max_drawdown:.2%}",
            f"-{metrics.max_drawdown*100:.1f}%"
        )
    
    with col4:
        st.metric(
            "胜率",
            f"{metrics.win_rate:.1%}",
            f"{metrics.profitable_trades}/{metrics.total_trades}"
        )


def _render_cumulative_returns_chart(start_date, end_date):
    """渲染累计收益曲线图"""
    st.subheader("📈 收益曲线")
    
    # 生成模拟收益曲线数据
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    cumulative_returns = np.cumsum(np.random.normal(0.001, 0.02, len(dates)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=cumulative_returns,
        mode='lines',
        name='累计收益',
        line=dict(color='#00D4AA', width=2)
    ))
    
    fig.update_layout(
        title="累计收益曲线",
        xaxis_title="日期",
        yaxis_title="累计收益率",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="cumulative_returns_chart")


def _render_backtest_analysis():
    """渲染历史回测标签页"""
    st.subheader("🔄 历史回测")
    
    # 回测参数设置
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_capital = st.number_input("初始资金 (USDT)", value=10000, min_value=1000)
    
    with col2:
        strategy_type = st.selectbox(
            "策略类型",
            ["现货套利", "三角套利", "跨链套利", "期现套利"]
        )
    
    with col3:
        risk_level = st.selectbox(
            "风险等级",
            ["保守", "平衡", "激进"]
        )
    
    # 运行回测
    if st.button("🚀 开始回测", key="start_backtest"):
        _run_backtest_simulation(strategy_type, initial_capital)


def _run_backtest_simulation(strategy_type: str, initial_capital: float):
    """运行回测模拟"""
    with st.spinner("正在运行历史回测..."):
        time.sleep(2)  # 模拟回测时间
        
        # 模拟回测结果
        backtest_result = BacktestResult(
            strategy_name=strategy_type,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            initial_capital=initial_capital,
            final_capital=initial_capital * 1.234,
            total_return=0.234,
            max_drawdown=0.067,
            sharpe_ratio=1.89,
            total_trades=456,
            win_rate=0.72
        )
        
        # 显示回测结果
        st.success("✅ 回测完成！")
        _display_backtest_results(backtest_result)


def _display_backtest_results(result: BacktestResult):
    """显示回测结果"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 回测概览")
        st.write(f"**策略名称**: {result.strategy_name}")
        st.write(f"**回测期间**: {result.start_date} 至 {result.end_date}")
        st.write(f"**初始资金**: ${result.initial_capital:,.2f}")
        st.write(f"**最终资金**: ${result.final_capital:,.2f}")
        st.write(f"**总收益**: ${result.final_capital - result.initial_capital:,.2f}")
    
    with col2:
        st.subheader("📈 关键指标")
        st.write(f"**总收益率**: {result.total_return:.2%}")
        st.write(f"**最大回撤**: {result.max_drawdown:.2%}")
        st.write(f"**夏普比率**: {result.sharpe_ratio:.2f}")
        st.write(f"**交易次数**: {result.total_trades}")
        st.write(f"**胜率**: {result.win_rate:.1%}")


def _render_strategy_optimization():
    """渲染策略优化标签页"""
    st.subheader("⚡ 策略优化")
    
    # 优化参数设置
    st.write("### 🎯 优化目标")
    
    col1, col2 = st.columns(2)
    
    with col1:
        optimization_target = st.selectbox(
            "优化目标",
            ["最大化收益", "最大化夏普比率", "最小化回撤", "最大化胜率"]
        )
    
    with col2:
        optimization_method = st.selectbox(
            "优化方法",
            ["网格搜索", "遗传算法", "贝叶斯优化", "粒子群优化"]
        )
    
    # 开始优化
    if st.button("🔍 开始优化", key="start_optimization"):
        _run_strategy_optimization(optimization_target, optimization_method)


def _run_strategy_optimization(target: str, method: str):
    """运行策略优化"""
    with st.spinner("正在进行策略优化..."):
        time.sleep(3)  # 模拟优化时间
        
        st.success("✅ 优化完成！")
        
        # 最优参数
        st.subheader("🏆 最优参数组合")
        
        optimal_params = {
            "收益阈值": "0.45%",
            "仓位大小": "35%",
            "最大持仓": "4个",
            "止损比例": "2.5%",
            "止盈比例": "8.0%"
        }
        
        for param, value in optimal_params.items():
            st.write(f"**{param}**: {value}")


def _render_market_analysis():
    """渲染市场分析标签页"""
    st.subheader("📈 市场分析")
    
    # 市场概览
    st.write("### 🌍 市场概览")
    _display_market_overview()
    
    st.markdown("---")
    
    # 市场深度分析
    st.write("### 📊 市场深度分析")
    _render_market_depth_analysis()


def _display_market_overview():
    """显示市场概览"""
    # 模拟市场数据
    market_data = {
        "BTC/USDT": {"price": 43250.67, "change_24h": 2.34, "volume": "1.2B"},
        "ETH/USDT": {"price": 2567.89, "change_24h": -1.23, "volume": "890M"},
        "BNB/USDT": {"price": 315.45, "change_24h": 0.87, "volume": "234M"},
        "ADA/USDT": {"price": 0.4567, "change_24h": 3.45, "volume": "156M"},
        "SOL/USDT": {"price": 98.76, "change_24h": -2.11, "volume": "445M"}
    }
    
    for symbol, data in market_data.items():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write(f"**{symbol}**")
        
        with col2:
            st.write(f"${data['price']:,.2f}")
        
        with col3:
            color = "green" if data['涨跌24h'] > 0 else "red"
            st.markdown(f"<span style='color: {color}'>{data['涨跌24h']:+.2f}%</span>", 
                       unsafe_allow_html=True)
        
        with col4:
            st.write(data['volume'])


def _render_market_depth_analysis():
    """渲染市场深度分析"""
    # 选择交易对和交易所
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_symbol = st.selectbox(
            "选择交易对",
            ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"],
            key="depth_symbol"
        )
    
    with col2:
        selected_exchange = st.selectbox(
            "选择交易所",
            ["Binance", "OKX", "Bybit", "Huobi", "KuCoin"],
            key="depth_exchange"
        )
    
    with col3:
        if st.button("🔍 分析市场深度", key="analyze_depth"):
            _analyze_market_depth(selected_exchange, selected_symbol)


def _analyze_market_depth(exchange: str, symbol: str):
    """分析市场深度"""
    with st.spinner("正在分析市场深度..."):
        # 模拟市场深度分析
        depth_data = market_depth_analyzer.analyze_order_book(exchange, symbol)
        
        if depth_data:
            st.success("✅ 市场深度分析完成")
            
            # 显示流动性指标
            _display_liquidity_metrics(depth_data)
            
            # 订单簿可视化
            _render_order_book_visualization()
            
            # 价格冲击分析
            _render_price_impact_analysis()
            
            # 最佳执行建议
            _render_execution_suggestions()
        else:
            st.error("❌ 无法获取市场深度数据")


def _display_liquidity_metrics(depth_data):
    """显示流动性指标"""
    st.write("#### 💧 流动性指标")
    
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    with metrics_col1:
        st.metric(
            "买单深度",
            f"${depth_data.bid_depth:,.2f}",
            delta=f"{depth_data.bid_depth_change:+.2f}%"
        )
    
    with metrics_col2:
        st.metric(
            "卖单深度", 
            f"${depth_data.ask_depth:,.2f}",
            delta=f"{depth_data.ask_depth_change:+.2f}%"
        )
    
    with metrics_col3:
        st.metric(
            "买卖价差",
            f"{depth_data.spread:.4f}",
            delta=f"{depth_data.spread_change:+.4f}"
        )
    
    with metrics_col4:
        st.metric(
            "流动性评分",
            f"{depth_data.liquidity_score:.1f}/10",
            delta=f"{depth_data.score_change:+.1f}"
        )


def _render_order_book_visualization():
    """渲染订单簿可视化"""
    st.write("#### 📈 订单簿分布")
    
    # 创建订单簿图表
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('买单深度', '卖单深度'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 买单数据
    bid_prices = [43245.50, 43245.00, 43244.50, 43244.00, 43243.50]
    bid_volumes = [2.5, 5.2, 3.8, 7.1, 4.6]
    
    # 卖单数据  
    ask_prices = [43246.00, 43246.50, 43247.00, 43247.50, 43248.00]
    ask_volumes = [3.2, 4.8, 6.1, 2.9, 5.5]
    
    fig.add_trace(
        go.Bar(
            x=bid_volumes,
            y=bid_prices,
            orientation='h',
            name='买单',
            marker_color='green',
            opacity=0.7
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=ask_volumes,
            y=ask_prices,
            orientation='h',
            name='卖单',
            marker_color='red',
            opacity=0.7
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_text="订单簿深度分析"
    )
    
    st.plotly_chart(fig, use_container_width=True, key="order_book_depth_analysis")


def _render_price_impact_analysis():
    """渲染价格冲击分析"""
    st.write("#### ⚡ 价格冲击分析")
    
    impact_col1, impact_col2 = st.columns(2)
    
    with impact_col1:
        st.write("**买入冲击成本**")
        buy_amounts = [1000, 5000, 10000, 50000, 100000]
        buy_impacts = [0.02, 0.08, 0.15, 0.45, 0.89]
        
        impact_df = pd.DataFrame({
            "交易金额 ($)": buy_amounts,
            "价格冲击 (%)": buy_impacts
        })
        st.dataframe(impact_df, use_container_width=True)
    
    with impact_col2:
        st.write("**卖出冲击成本**")
        sell_amounts = [1000, 5000, 10000, 50000, 100000]
        sell_impacts = [0.03, 0.09, 0.18, 0.52, 0.95]
        
        impact_df = pd.DataFrame({
            "交易金额 ($)": sell_amounts,
            "价格冲击 (%)": sell_impacts
        })
        st.dataframe(impact_df, use_container_width=True)


def _render_execution_suggestions():
    """渲染最佳执行建议"""
    st.write("#### 🎯 最佳执行建议")
    
    suggestion_col1, suggestion_col2 = st.columns(2)
    
    with suggestion_col1:
        st.info("""
        **💡 执行策略建议**
        - 大额订单建议分批执行
        - 当前流动性较好，适合中等规模交易
        - 建议在买一卖一价格附近挂单
        """)
    
    with suggestion_col2:
        st.warning("""
        **⚠️ 风险提示**
        - 大额交易可能造成显著价格冲击
        - 注意监控订单簿变化
        - 考虑使用算法交易降低冲击
        """)