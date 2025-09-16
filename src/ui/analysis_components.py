"""
分析组件模块
包含资金费率分析、订单簿分析、风险仪表盘等功能组件
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any
import asyncio

from src.utils.async_utils import safe_run_async


def render_funding_rate_analysis(funding_rate_provider):
    """渲染资金费率分析界面"""
    st.subheader("💰 资金费率套利分析")
    
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
        _display_funding_rate_results(st.session_state['funding_data'], min_rate_diff, funding_rate_provider)
    else:
        st.info("📊 点击上方按钮获取最新的资金费率数据")


def _display_funding_rate_results(funding_data: Dict, min_rate_diff: float, funding_rate_provider):
    """显示资金费率分析结果"""
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
        _render_funding_rate_charts(funding_data)
        _render_funding_rate_strategy_info()
        
    else:
        st.info(f"🔍 当前没有满足条件的资金费率套利机会（最小费率差异: {min_rate_diff}%）")


def _render_funding_rate_charts(funding_data: Dict):
    """渲染资金费率图表"""
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


def _render_funding_rate_strategy_info():
    """渲染资金费率策略说明"""
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


def render_orderbook_analysis(orderbook_analyzer):
    """渲染订单簿深度与滑点分析界面"""
    st.subheader("📊 订单簿深度与滑点分析")
    
    # 控制面板
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_symbol = st.selectbox(
            "选择交易对",
            ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT'],
            key="orderbook_symbol"
        )
    
    with col2:
        trade_amount = st.number_input(
            "交易金额 (USDT)",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000,
            key="trade_amount"
        )
    
    with col3:
        selected_exchanges = st.multiselect(
            "选择交易所",
            ['binance', 'okx', 'bybit', 'gate', 'kucoin'],
            default=['binance', 'okx', 'bybit'],
            key="orderbook_exchanges"
        )
    
    with col4:
        analysis_side = st.selectbox(
            "交易方向",
            ['buy', 'sell'],
            format_func=lambda x: '买入' if x == 'buy' else '卖出',
            key="analysis_side"
        )
    
    if st.button("🔍 分析订单簿深度", width='stretch'):
        if not selected_exchanges:
            st.error("请至少选择一个交易所")
        else:
            with st.spinner("正在获取订单簿数据并分析滑点..."):
                # 获取跨交易所滑点分析
                slippage_analysis = safe_run_async(
                    orderbook_analyzer.analyze_cross_exchange_slippage(selected_symbol, trade_amount)
                )
                
                if slippage_analysis:
                    st.session_state['slippage_analysis'] = slippage_analysis
                    st.session_state['analysis_params'] = {
                        'symbol': selected_symbol,
                        'amount': trade_amount,
                        'side': analysis_side,
                        'timestamp': datetime.now()
                    }
                    st.success(f"✅ 成功分析 {len([ex for ex in slippage_analysis if 'error' not in slippage_analysis[ex]])} 个交易所的订单簿数据")
                else:
                    st.error("❌ 获取订单簿数据失败")
    
    # 显示分析结果
    if 'slippage_analysis' in st.session_state and st.session_state['slippage_analysis']:
        _display_orderbook_analysis_results(
            st.session_state['slippage_analysis'], 
            selected_exchanges, 
            analysis_side,
            trade_amount,
            orderbook_analyzer
        )
    else:
        st.info("📊 点击上方按钮开始分析订单簿深度")


def _display_orderbook_analysis_results(analysis_data: Dict, selected_exchanges: List[str], 
                                       analysis_side: str, trade_amount: float, orderbook_analyzer):
    """显示订单簿分析结果"""
    params = st.session_state.get('analysis_params', {})
    st.info(f"📊 分析时间: {params.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 过滤选中的交易所
    filtered_data = {ex: data for ex, data in analysis_data.items() if ex in selected_exchanges}
    
    # 创建滑点对比表格
    st.subheader(f"💹 {analysis_side.upper()} 滑点分析对比")
    
    comparison_data = []
    for exchange, data in filtered_data.items():
        if 'error' in data:
            comparison_data.append({
                '交易所': exchange.upper(),
                '状态': '❌ 数据获取失败',
                '最优价格': '-',
                '平均价格': '-',
                '滑点 (%)': '-',
                '价格影响 (%)': '-',
                '成交率 (%)': '-'
            })
        elif analysis_side in data:
            side_data = data[analysis_side]
            if 'error' in side_data:
                comparison_data.append({
                    '交易所': exchange.upper(),
                    '状态': f"❌ {side_data['error']}",
                    '最优价格': '-',
                    '平均价格': '-',
                    '滑点 (%)': '-',
                    '价格影响 (%)': '-',
                    '成交率 (%)': '-'
                })
            else:
                comparison_data.append({
                    '交易所': exchange.upper(),
                    '状态': '✅ 正常',
                    '最优价格': f"${side_data['best_price']:.4f}",
                    '平均价格': f"${side_data['average_price']:.4f}",
                    '滑点 (%)': f"{side_data['slippage_pct']:.4f}%",
                    '价格影响 (%)': f"{side_data['price_impact_pct']:.4f}%",
                    '成交率 (%)': f"{side_data['fill_rate']:.2f}%"
                })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # 显示最优执行策略
        _display_optimal_execution_strategy(filtered_data, trade_amount, orderbook_analyzer)
        
        # 滑点可视化
        _render_slippage_visualization(filtered_data, analysis_side, params.get('symbol', ''))
        
        # 策略说明
        _render_slippage_strategy_info()
    else:
        st.info("📊 没有可用的订单簿数据")


def _display_optimal_execution_strategy(filtered_data: Dict, trade_amount: float, orderbook_analyzer):
    """显示最优执行策略"""
    st.subheader("🎯 最优执行策略推荐")
    
    strategy_result = orderbook_analyzer.find_optimal_execution_strategy(
        filtered_data, trade_amount
    )
    
    if strategy_result['optimal_strategy']:
        optimal = strategy_result['optimal_strategy']
        
        if optimal['type'] == 'single_exchange':
            st.success(f"""**推荐策略：单一交易所执行**
            
            - 🏆 **最优交易所**: {optimal['exchange'].upper()}
            - 💰 **预期平均价格**: ${optimal['avg_price']:.4f}
            - 📉 **预期滑点**: {optimal['slippage_pct']:.4f}%
            - ✅ **预期成交率**: {optimal['fill_rate']:.2f}%
            """)
        
        elif optimal['type'] == 'split_execution':
            exchanges_str = ' + '.join([ex.upper() for ex in optimal['exchanges']])
            st.success(f"""**推荐策略：分割执行**
            
            - 🏆 **交易所组合**: {exchanges_str}
            - 💰 **预期平均价格**: ${optimal['avg_price']:.4f}
            - 📉 **预期滑点**: {optimal['slippage_pct']:.4f}%
            - ⚖️ **分割比例**: {optimal['split_ratio']}
            """)
        
        # 显示所有策略对比
        with st.expander("📋 所有策略对比"):
            all_strategies = strategy_result['all_strategies']
            if all_strategies:
                strategy_df_data = []
                for i, strategy in enumerate(all_strategies):
                    if strategy['type'] == 'single_exchange':
                        strategy_df_data.append({
                            '排名': i + 1,
                            '策略类型': '单一交易所',
                            '交易所': strategy['exchange'].upper(),
                            '平均价格': f"${strategy['avg_price']:.4f}",
                            '滑点 (%)': f"{strategy['slippage_pct']:.4f}%",
                            '成交率 (%)': f"{strategy['fill_rate']:.2f}%"
                        })
                    elif strategy['type'] == 'split_execution':
                        exchanges_str = ' + '.join([ex.upper() for ex in strategy['exchanges']])
                        strategy_df_data.append({
                            '排名': i + 1,
                            '策略类型': '分割执行',
                            '交易所': exchanges_str,
                            '平均价格': f"${strategy['avg_price']:.4f}",
                            '滑点 (%)': f"{strategy['slippage_pct']:.4f}%",
                            '成交率 (%)': '-'
                        })
                
                strategy_df = pd.DataFrame(strategy_df_data)
                st.dataframe(strategy_df, width='stretch', hide_index=True)
    else:
        st.warning("⚠️ 未找到可行的执行策略")


def _render_slippage_visualization(filtered_data: Dict, analysis_side: str, symbol: str):
    """渲染滑点可视化图表"""
    st.subheader("📈 滑点可视化分析")
    
    # 创建滑点对比图表
    valid_exchanges = []
    slippage_values = []
    price_impact_values = []
    
    for exchange, data in filtered_data.items():
        if 'error' not in data and analysis_side in data and 'error' not in data[analysis_side]:
            valid_exchanges.append(exchange.upper())
            slippage_values.append(data[analysis_side]['slippage_pct'])
            price_impact_values.append(data[analysis_side]['price_impact_pct'])
    
    if valid_exchanges:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='滑点 (%)',
            x=valid_exchanges,
            y=slippage_values,
            text=[f"{val:.4f}%" for val in slippage_values],
            textposition='auto',
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='价格影响 (%)',
            x=valid_exchanges,
            y=price_impact_values,
            text=[f"{val:.4f}%" for val in price_impact_values],
            textposition='auto',
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title=f"{symbol} {analysis_side.upper()} 滑点与价格影响对比",
            xaxis_title="交易所",
            yaxis_title="百分比 (%)",
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, width='stretch', key="slippage_analysis_chart")


def _render_slippage_strategy_info():
    """渲染滑点分析策略说明"""
    with st.expander("💡 滑点分析说明"):
        st.markdown("""
        **关键指标解释：**
        
        1. **滑点 (Slippage)**：实际成交价格与最优价格的差异
            - 反映了订单簿深度对大额交易的影响
            - 滑点越小，交易成本越低
        
        2. **价格影响 (Price Impact)**：从最优价格到最差成交价格的变化
            - 显示了订单对市场价格的冲击程度
            - 价格影响越小，市场深度越好
        
        3. **成交率 (Fill Rate)**：订单能够完全成交的比例
            - 100%表示订单能够完全成交
            - 低于100%表示订单簿深度不足
        
        **交易建议：**
        - 大额交易建议选择滑点最小的交易所
        - 考虑分割订单到多个交易所以降低价格影响
        - 关注成交率，避免在深度不足的交易所执行大额订单
        - 实际交易时还需考虑手续费、转账成本等因素
        """)


def render_risk_dashboard(risk_dashboard):
    """渲染动态风险仪表盘"""
    st.subheader("📊 动态风险仪表盘")
    
    # 控制面板
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_exchanges = st.multiselect(
                "选择交易所",
                ["binance", "okx", "bybit", "huobi", "coinbase"],
                default=["binance", "okx"]
            )
        
        with col2:
            selected_symbols = st.multiselect(
                "选择交易对",
                ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"],
                default=["BTC/USDT", "ETH/USDT"]
            )
        
        with col3:
            risk_timeframe = st.selectbox(
                "风险评估周期",
                ["1h", "4h", "1d", "7d", "30d"],
                index=2
            )
        
        with col4:
            portfolio_value = st.number_input(
                "投资组合价值 (USDT)",
                min_value=100.0,
                value=10000.0,
                step=100.0
            )
    
    # 风险分析按钮
    if st.button("🔍 开始风险分析", type="primary", use_container_width=True):
        with st.spinner("正在分析风险指标..."):
            try:
                # 获取风险仪表盘数据
                dashboard_data = risk_dashboard.get_dashboard_data(
                    exchanges=selected_exchanges,
                    symbols=selected_symbols,
                    timeframe=risk_timeframe
                )
                
                if dashboard_data:
                    _display_risk_overview(dashboard_data, portfolio_value)
                    _display_detailed_risk_metrics(dashboard_data)
                else:
                    st.error("❌ 获取风险数据失败")
            except Exception as e:
                st.error(f"❌ 风险分析失败: {str(e)}")
    else:
        st.info("📊 点击上方按钮开始风险分析")


def _display_risk_overview(dashboard_data: Dict, portfolio_value: float):
    """显示风险概览"""
    st.subheader("📈 风险概览")
    
    # 总体风险指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overall_risk = dashboard_data.get('overall_risk_level', 'medium')
        risk_color = {'low': 'green', 'medium': 'orange', 'high': 'red'}.get(overall_risk, 'orange')
        st.metric(
            "总体风险等级",
            overall_risk.upper(),
            delta=None,
            delta_color=risk_color
        )
    
    with col2:
        portfolio_var = dashboard_data.get('portfolio_var', 0)
        st.metric(
            "投资组合VaR (95%)",
            f"${portfolio_var:,.2f}",
            delta=f"{(portfolio_var/portfolio_value)*100:.2f}%"
        )
    
    with col3:
        avg_volatility = dashboard_data.get('average_volatility', 0)
        st.metric(
            "平均波动率",
            f"{avg_volatility:.2f}%",
            delta=None
        )
    
    with col4:
        correlation_risk = dashboard_data.get('correlation_risk', 0)
        st.metric(
            "相关性风险",
            f"{correlation_risk:.2f}",
            delta=None
        )


def _display_detailed_risk_metrics(dashboard_data: Dict):
    """显示详细风险指标"""
    st.subheader("📊 详细风险指标")
    
    risk_metrics = dashboard_data.get('risk_metrics', [])
    if risk_metrics:
        risk_df = pd.DataFrame(risk_metrics)
        st.dataframe(
            risk_df,
            use_container_width=True,
            column_config={
                "symbol": "交易对",
                "exchange": "交易所",
                "volatility": st.column_config.NumberColumn(
                    "波动率 (%)",
                    format="%.2f"
                ),
                "var_95": st.column_config.NumberColumn(
                    "VaR 95% (%)",
                    format="%.2f"
                ),
                "max_drawdown": st.column_config.NumberColumn(
                    "最大回撤 (%)",
                    format="%.2f"
                ),
                "sharpe_ratio": st.column_config.NumberColumn(
                    "夏普比率",
                    format="%.2f"
                )
            }
        )
    else:
        st.info("📊 没有可用的风险指标数据")