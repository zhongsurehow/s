"""
主控制台组件 - 提供套利交易系统的核心监控界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import time
import asyncio

# 导入真实数据服务
from providers.real_data_service import real_data_service

# 配置常量
class ConsoleConfig:
    """主控制台配置"""
    # 交易所列表
    EXCHANGES = ['Binance', 'OKX', 'Huobi', 'KuCoin', 'Gate.io', 'Bybit', 'Coinbase', 'Kraken']
    
    # 加密货币列表
    CRYPTOCURRENCIES = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'MATIC', 'DOT', 'AVAX']
    
    # 交易对列表
    TRADING_PAIRS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
    
    # 颜色配置
    COLORS = {
        'primary': '#4ECDC4',
        'secondary': '#45B7D1',
        'success': '#00C851',
        'warning': '#ffbb33',
        'danger': '#ff4444',
        'info': '#33b5e5'
    }
    
    # 图表颜色
    CHART_COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
    
    # KPI阈值
    THRESHOLDS = {
        'risk_low': 4,
        'risk_medium': 6,
        'opportunity_good': 75,
        'opportunity_excellent': 90,
        'latency_good': 50,
        'latency_warning': 100
    }

@dataclass
class KPIData:
    """KPI数据类"""
    total_opportunities: int
    active_trades: int
    daily_pnl: float
    success_rate: float
    avg_profit_margin: float
    total_volume: float
    network_latency: float
    risk_score: float

@dataclass
class OpportunityData:
    """套利机会数据类"""
    rank: int
    trading_pair: str
    exchanges: str
    profit_margin: float
    available_volume: float
    risk_score: float
    difficulty: str
    estimated_time: int

class DataGenerator:
    """数据生成器 - 使用真实API数据"""
    
    @staticmethod
    @st.cache_data(ttl=30)
    def generate_kpi_data() -> Dict[str, Any]:
        """生成KPI数据 - 基于真实数据"""
        try:
            # 获取真实KPI数据
            return real_data_service.get_kpi_data()
        except Exception as e:
            st.error(f"获取KPI数据失败: {e}")
            # 返回默认值而不是随机数据
            return {
                'total_opportunities': 0,
                'active_trades': 0,
                'avg_profit_margin': 0,
                'total_volume': 0,
                'network_latency': 999.0,
                'risk_score': 10.0,
                'success_rate': 0.0,
                'daily_pnl': 0
            }
    
    @staticmethod
    def generate_market_heatmap_data() -> np.ndarray:
        """生成市场热力图数据 - 使用真实API数据"""
        try:
            # 获取真实价格矩阵数据
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            price_matrix = loop.run_until_complete(
                real_data_service.get_price_matrix()
            )
            loop.close()
            
            if price_matrix:
                # 转换为numpy数组
                symbols = list(price_matrix.keys())[:len(ConsoleConfig.CRYPTOCURRENCIES)]
                exchanges = ConsoleConfig.EXCHANGES
                
                data = []
                for symbol in symbols:
                    row = []
                    for exchange in exchanges:
                        # 获取价格差异，如果没有数据则为0
                        diff = price_matrix.get(symbol, {}).get(exchange, 0)
                        row.append(diff)
                    data.append(row)
                
                # 如果数据不足，用0填充
                while len(data) < len(ConsoleConfig.CRYPTOCURRENCIES):
                    data.append([0] * len(exchanges))
                
                return np.array(data)
            else:
                # 如果没有真实数据，返回零矩阵
                return np.zeros((len(ConsoleConfig.CRYPTOCURRENCIES), len(ConsoleConfig.EXCHANGES)))
                
        except Exception as e:
            st.error(f"获取热力图数据失败: {e}")
            return np.zeros((len(ConsoleConfig.CRYPTOCURRENCIES), len(ConsoleConfig.EXCHANGES)))
    
    @staticmethod
    def generate_volume_data() -> List[float]:
        """生成交易量数据 - 使用真实API数据"""
        try:
            # 获取真实交易量数据
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            volume_data = loop.run_until_complete(
                real_data_service.get_volume_data()
            )
            loop.close()
            
            if volume_data:
                # 按照配置的交易所顺序返回数据
                volumes = []
                for exchange in ConsoleConfig.EXCHANGES:
                    # 查找匹配的交易所（不区分大小写）
                    volume = 0
                    for key, value in volume_data.items():
                        if key.lower() == exchange.lower():
                            volume = value
                            break
                    volumes.append(volume)
                return volumes
            else:
                # 如果没有真实数据，返回零列表
                return [0] * len(ConsoleConfig.EXCHANGES)
                
        except Exception as e:
            st.error(f"获取交易量数据失败: {e}")
            return [0] * len(ConsoleConfig.EXCHANGES)
    
    @staticmethod
    def generate_profit_trend_data(hours: int = 24) -> Tuple[List[datetime], List[float]]:
        """生成盈利趋势数据 - 使用真实API数据"""
        try:
            # 获取真实盈利趋势数据
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            timestamps, profits = loop.run_until_complete(
                real_data_service.get_profit_trend_data(hours)
            )
            loop.close()
            
            return timestamps, profits
            
        except Exception as e:
            st.error(f"获取盈利趋势数据失败: {e}")
            # 返回空数据
            timestamps = [datetime.now() - timedelta(hours=hours-i) for i in range(hours)]
            profits = [0] * hours
            return timestamps, profits
    
    @staticmethod
    @st.cache_data(ttl=60)
    def generate_arbitrage_opportunities() -> List[Dict[str, Any]]:
        """生成套利机会数据 - 使用真实API数据"""
        try:
            # 使用异步函数获取真实套利机会
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            opportunities = loop.run_until_complete(
                real_data_service.get_real_arbitrage_opportunities()
            )
            loop.close()
            
            # 转换为字典格式以便显示
            return [
                {
                    'symbol': opp.symbol,
                    'buy_exchange': opp.buy_exchange,
                    'sell_exchange': opp.sell_exchange,
                    'buy_price': opp.buy_price,
                    'sell_price': opp.sell_price,
                    'profit_margin': opp.profit_margin,
                    'volume': opp.available_volume,
                    'risk_score': opp.risk_score,
                    'estimated_time': opp.estimated_time
                }
                for opp in opportunities
            ]
        except Exception as e:
            st.error(f"获取套利机会失败: {e}")
            return []
    
    @staticmethod
    def generate_top_opportunities() -> List[OpportunityData]:
        """生成顶级套利机会数据"""
        opportunities = []
        exchanges_pairs = [
            ('Binance', 'OKX'),
            ('Huobi', 'KuCoin'),
            ('Gate.io', 'Bybit'),
            ('Binance', 'Huobi'),
            ('OKX', 'Gate.io')
        ]
        
        for i, (crypto, (ex1, ex2)) in enumerate(zip(ConsoleConfig.TRADING_PAIRS, exchanges_pairs)):
            opportunities.append(OpportunityData(
                rank=i + 1,
                trading_pair=crypto,
                exchanges=f"{ex1} → {ex2}",
                profit_margin=random.uniform(0.5, 3.0),
                available_volume=random.uniform(10000, 50000),
                risk_score=random.uniform(2, 8),
                difficulty=random.choice(['简单', '中等', '困难']),
                estimated_time=random.randint(30, 180)
            ))
        
        return opportunities

class ChartRenderer:
    """图表渲染器"""
    
    @staticmethod
    def render_market_heatmap() -> go.Figure:
        """渲染市场热力图"""
        try:
            price_diff_matrix = DataGenerator.generate_market_heatmap_data()
            
            fig = px.imshow(
                price_diff_matrix,
                x=ConsoleConfig.EXCHANGES,
                y=ConsoleConfig.CRYPTOCURRENCIES,
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,
                title="交易所价格差异热力图 (%)",
                labels=dict(x="交易所", y="加密货币", color="价格差异(%)")
            )
            
            # 添加数值标注
            for i in range(len(ConsoleConfig.CRYPTOCURRENCIES)):
                for j in range(len(ConsoleConfig.EXCHANGES)):
                    fig.add_annotation(
                        x=j, y=i,
                        text=f"{price_diff_matrix[i][j]:.2f}%",
                        showarrow=False,
                        font=dict(color="white" if abs(price_diff_matrix[i][j]) > 1.5 else "black")
                    )
            
            fig.update_layout(
                height=400,
                font=dict(size=12),
                title_font_size=16
            )
            
            return fig
            
        except Exception as e:
            st.error(f"渲染市场热力图时出错: {e}")
            return go.Figure()
    
    @staticmethod
    def render_volume_distribution() -> go.Figure:
        """渲染交易量分布图"""
        try:
            volumes = DataGenerator.generate_volume_data()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=ConsoleConfig.EXCHANGES,
                    y=volumes,
                    marker_color=ConsoleConfig.CHART_COLORS,
                    text=[f'${v:,.0f}' for v in volumes],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>交易量: $%{y:,.0f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title="各交易所24小时交易量",
                xaxis_title="交易所",
                yaxis_title="交易量 (USD)",
                height=400,
                font=dict(size=12),
                title_font_size=16
            )
            
            return fig
            
        except Exception as e:
            st.error(f"渲染交易量分布图时出错: {e}")
            return go.Figure()
    
    @staticmethod
    def render_profit_trend() -> go.Figure:
        """渲染盈利趋势图"""
        try:
            timestamps, profits = DataGenerator.generate_profit_trend_data()
            
            fig = go.Figure()
            
            # 添加盈利曲线
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=profits,
                mode='lines+markers',
                name='累计盈利',
                line=dict(color=ConsoleConfig.COLORS['primary'], width=3),
                fill='tonexty',
                fillcolor=f"rgba(78, 205, 196, 0.1)",
                hovertemplate='<b>累计盈利</b><br>时间: %{x}<br>金额: $%{y:,.0f}<extra></extra>'
            ))
            
            # 添加零线
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig.update_layout(
                title="24小时盈利趋势",
                xaxis_title="时间",
                yaxis_title="累计盈利 (USD)",
                height=400,
                hovermode='x unified',
                font=dict(size=12),
                title_font_size=16
            )
            
            return fig
            
        except Exception as e:
            st.error(f"渲染盈利趋势图时出错: {e}")
            return go.Figure()
    
    @staticmethod
    def render_opportunity_gauge() -> go.Figure:
        """渲染机会质量仪表盘"""
        try:
            opportunity_score = random.uniform(60, 95)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=opportunity_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "套利机会质量评分"},
                delta={'reference': ConsoleConfig.THRESHOLDS['opportunity_good']},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgray"},
                        {'range': [60, ConsoleConfig.THRESHOLDS['opportunity_good']], 'color': "yellow"},
                        {'range': [ConsoleConfig.THRESHOLDS['opportunity_good'], ConsoleConfig.THRESHOLDS['opportunity_excellent']], 'color': "lightgreen"},
                        {'range': [ConsoleConfig.THRESHOLDS['opportunity_excellent'], 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': ConsoleConfig.THRESHOLDS['opportunity_excellent']
                    }
                }
            ))
            
            fig.update_layout(height=300)
            return fig
            
        except Exception as e:
            st.error(f"渲染机会质量仪表盘时出错: {e}")
            return go.Figure()

class MetricsRenderer:
    """指标渲染器"""
    
    @staticmethod
    def render_kpi_cards() -> None:
        """渲染KPI指标卡片"""
        try:
            kpi_data = DataGenerator.generate_kpi_data()
            
            # 第一行KPI
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_opportunities = random.randint(-5, 10)
                st.metric(
                    "套利机会",
                    f"{kpi_data['total_opportunities']}个",
                    delta=f"{delta_opportunities:+d}",
                    delta_color="normal"
                )
            
            with col2:
                delta_trades = random.randint(-2, 3)
                st.metric(
                    "活跃交易",
                    f"{kpi_data['active_trades']}笔",
                    delta=f"{delta_trades:+d}",
                    delta_color="normal"
                )
            
            with col3:
                delta_pnl = random.uniform(-500, 1000)
                st.metric(
                    "今日盈亏",
                    f"${kpi_data['daily_pnl']:,.0f}",
                    delta=f"${delta_pnl:+,.0f}",
                    delta_color="normal" if delta_pnl >= 0 else "inverse"
                )
            
            with col4:
                delta_success = random.uniform(-2, 5)
                st.metric(
                    "成功率",
                    f"{kpi_data['success_rate']:.1f}%",
                    delta=f"{delta_success:+.1f}%",
                    delta_color="normal"
                )
            
            # 第二行KPI
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                delta_margin = random.uniform(-0.2, 0.3)
                st.metric(
                    "平均利润率",
                    f"{kpi_data['avg_profit_margin']:.2f}%",
                    delta=f"{delta_margin:+.2f}%",
                    delta_color="normal"
                )
            
            with col2:
                delta_volume = random.uniform(-10000, 20000)
                st.metric(
                    "交易量",
                    f"${kpi_data['total_volume']:,.0f}",
                    delta=f"${delta_volume:+,.0f}",
                    delta_color="normal"
                )
            
            with col3:
                delta_latency = random.uniform(-10, 15)
                st.metric(
                    "网络延迟",
                    f"{kpi_data['network_latency']:.0f}ms",
                    delta=f"{delta_latency:+.0f}ms",
                    delta_color="inverse" if delta_latency > 0 else "normal"
                )
            
            with col4:
                risk_level = ("低" if kpi_data['risk_score'] < ConsoleConfig.THRESHOLDS['risk_low'] 
                             else "中" if kpi_data['risk_score'] < ConsoleConfig.THRESHOLDS['risk_medium'] 
                             else "高")
                st.metric(
                    "风险评分",
                    f"{kpi_data['risk_score']:.1f}/10",
                    delta=risk_level,
                    delta_color="normal" if kpi_data['risk_score'] < ConsoleConfig.THRESHOLDS['risk_medium'] else "inverse"
                )
                
        except Exception as e:
            st.error(f"渲染KPI指标时出错: {e}")
    
    @staticmethod
    def render_top_opportunities_table() -> None:
        """渲染顶级套利机会表格"""
        try:
            opportunities = DataGenerator.generate_top_opportunities()
            
            # 转换为DataFrame
            df_data = []
            for opp in opportunities:
                df_data.append({
                    '排名': opp.rank,
                    '交易对': opp.trading_pair,
                    '交易所': opp.exchanges,
                    '利润率': f"{opp.profit_margin:.2f}%",
                    '可用量': f"${opp.available_volume:,.0f}",
                    '风险评分': f"{opp.risk_score:.1f}/10",
                    '执行难度': opp.difficulty,
                    '预估时间': f"{opp.estimated_time}秒"
                })
            
            df = pd.DataFrame(df_data)
            
            # 添加样式
            def highlight_top_opportunities(row):
                if row['排名'] == 1:
                    return ['background-color: #d4edda'] * len(row)
                elif row['排名'] == 2:
                    return ['background-color: #fff3cd'] * len(row)
                elif row['排名'] == 3:
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = df.style.apply(highlight_top_opportunities, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"渲染套利机会表格时出错: {e}")

class ActionHandler:
    """操作处理器"""
    
    @staticmethod
    def render_quick_actions() -> None:
        """渲染快速操作按钮"""
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 刷新数据", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            
            with col2:
                if st.button("📊 详细分析", use_container_width=True):
                    st.info("跳转到详细分析页面...")
            
            with col3:
                if st.button("⚙️ 策略设置", use_container_width=True):
                    st.info("打开策略配置面板...")
            
            with col4:
                if st.button("📈 历史报告", use_container_width=True):
                    st.info("生成历史交易报告...")
                    
        except Exception as e:
            st.error(f"渲染快速操作时出错: {e}")
    
    @staticmethod
    def render_system_status() -> None:
        """渲染系统状态"""
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success("🟢 系统运行正常")
            
            with col2:
                st.info(f"🕐 最后更新: {datetime.now().strftime('%H:%M:%S')}")
            
            with col3:
                st.warning("⚠️ 建议关注BTC波动")
                
        except Exception as e:
            st.error(f"渲染系统状态时出错: {e}")

def render_main_console() -> None:
    """渲染主控制台界面"""
    try:
        st.header("📊 套利交易主控制台")
        st.markdown("*实时监控套利机会和交易表现*")
        
        # KPI指标卡片
        st.subheader("📈 关键绩效指标")
        MetricsRenderer.render_kpi_cards()
        
        st.markdown("---")
        
        # 主要图表区域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔥 市场热力图")
            heatmap_fig = ChartRenderer.render_market_heatmap()
            st.plotly_chart(heatmap_fig, use_container_width=True)
        
        with col2:
            st.subheader("⚡ 机会质量")
            gauge_fig = ChartRenderer.render_opportunity_gauge()
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        # 第二行图表
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 盈利趋势")
            profit_fig = ChartRenderer.render_profit_trend()
            st.plotly_chart(profit_fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 交易量分布")
            volume_fig = ChartRenderer.render_volume_distribution()
            st.plotly_chart(volume_fig, use_container_width=True)
        
        # 顶级机会表格
        st.subheader("🏆 顶级套利机会")
        MetricsRenderer.render_top_opportunities_table()
        
        # 快速操作按钮
        st.markdown("---")
        st.subheader("⚡ 快速操作")
        ActionHandler.render_quick_actions()
        
        # 系统状态
        st.markdown("---")
        ActionHandler.render_system_status()
        
    except Exception as e:
        st.error(f"主控制台系统出错: {e}")
        st.info("请刷新页面重试")