"""
网络监控组件 - 提供实时网络延迟监控和分析功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from functools import lru_cache

# 配置常量
class NetworkConfig:
    """网络监控配置"""
    EXCHANGES = ['Binance', 'OKX', 'Huobi', 'KuCoin', 'Gate.io', 'Bybit', 'Coinbase', 'Kraken']
    REGIONS = ['Asia', 'Europe', 'Americas']
    
    # 延迟阈值
    EXCELLENT_THRESHOLD = 50
    GOOD_THRESHOLD = 100
    FAIR_THRESHOLD = 150
    
    # 基础延迟配置
    BASE_LATENCY = {
        'Binance': {'Asia': 20, 'Europe': 80, 'Americas': 120},
        'OKX': {'Asia': 25, 'Europe': 85, 'Americas': 125},
        'Huobi': {'Asia': 30, 'Europe': 90, 'Americas': 130},
        'KuCoin': {'Asia': 35, 'Europe': 95, 'Americas': 135},
        'Gate.io': {'Asia': 40, 'Europe': 100, 'Americas': 140},
        'Bybit': {'Asia': 22, 'Europe': 82, 'Americas': 122},
        'Coinbase': {'Asia': 150, 'Europe': 50, 'Americas': 30},
        'Kraken': {'Asia': 160, 'Europe': 45, 'Americas': 35}
    }
    
    # 颜色配置
    COLORS = {
        'excellent': '#00C851',
        'good': '#ffbb33',
        'fair': '#ff8800',
        'poor': '#ff4444'
    }

@dataclass
class NetworkMetrics:
    """网络指标数据类"""
    exchange: str
    region: str
    latency: float
    packet_loss: float
    jitter: float
    status: str
    color: str
    timestamp: datetime

class NetworkDataGenerator:
    """网络数据生成器"""
    
    @staticmethod
    def _get_latency_status(latency: float) -> Tuple[str, str]:
        """根据延迟值获取状态和颜色"""
        if latency < NetworkConfig.EXCELLENT_THRESHOLD:
            return "优秀", NetworkConfig.COLORS['excellent']
        elif latency < NetworkConfig.GOOD_THRESHOLD:
            return "良好", NetworkConfig.COLORS['good']
        elif latency < NetworkConfig.FAIR_THRESHOLD:
            return "一般", NetworkConfig.COLORS['fair']
        else:
            return "较差", NetworkConfig.COLORS['poor']
    
    @staticmethod
    @lru_cache(maxsize=32)
    def generate_current_latency() -> pd.DataFrame:
        """生成当前网络延迟数据"""
        data = []
        current_time = datetime.now()
        
        for exchange in NetworkConfig.EXCHANGES:
            for region in NetworkConfig.REGIONS:
                try:
                    base = NetworkConfig.BASE_LATENCY[exchange][region]
                    current_latency = max(5, base + random.gauss(0, 15))
                    status, color = NetworkDataGenerator._get_latency_status(current_latency)
                    
                    metrics = NetworkMetrics(
                        exchange=exchange,
                        region=region,
                        latency=current_latency,
                        packet_loss=max(0, random.gauss(0.5, 0.3)),
                        jitter=max(0, random.gauss(5, 2)),
                        status=status,
                        color=color,
                        timestamp=current_time
                    )
                    
                    data.append(metrics.__dict__)
                    
                except Exception as e:
                    st.error(f"生成 {exchange}-{region} 数据时出错: {e}")
                    continue
        
        return pd.DataFrame(data)
    
    @staticmethod
    def generate_historical_latency(hours: int = 24) -> pd.DataFrame:
        """生成历史延迟数据"""
        exchanges = ['Binance', 'OKX', 'Huobi', 'KuCoin']
        data = []
        base_time = datetime.now() - timedelta(hours=hours)
        
        try:
            for i in range(hours * 60):  # 每分钟一个数据点
                timestamp = base_time + timedelta(minutes=i)
                
                for exchange in exchanges:
                    # 模拟日周期变化
                    hour = timestamp.hour
                    base_latency = 30 + 20 * np.sin(2 * np.pi * hour / 24)
                    noise = random.gauss(0, 10)
                    latency = max(5, base_latency + noise)
                    
                    data.append({
                        'timestamp': timestamp,
                        'exchange': exchange,
                        'latency': latency
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            st.error(f"生成历史数据时出错: {e}")
            return pd.DataFrame()

class NetworkChartRenderer:
    """网络图表渲染器"""
    
    @staticmethod
    def render_latency_heatmap(df: pd.DataFrame) -> go.Figure:
        """渲染延迟热力图"""
        try:
            pivot_df = df.pivot(index='exchange', columns='region', values='latency')
            
            fig = px.imshow(
                pivot_df,
                color_continuous_scale='RdYlGn_r',
                title="交易所网络延迟热力图 (ms)",
                labels=dict(x="地区", y="交易所", color="延迟(ms)")
            )
            
            fig.update_layout(
                height=400,
                font=dict(size=12),
                title_font_size=16
            )
            
            return fig
            
        except Exception as e:
            st.error(f"渲染热力图时出错: {e}")
            return go.Figure()
    
    @staticmethod
    def render_latency_trend(df_historical: pd.DataFrame) -> go.Figure:
        """渲染延迟趋势图"""
        try:
            fig = go.Figure()
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            for i, exchange in enumerate(df_historical['exchange'].unique()):
                exchange_data = df_historical[df_historical['exchange'] == exchange]
                
                fig.add_trace(go.Scatter(
                    x=exchange_data['timestamp'],
                    y=exchange_data['latency'],
                    mode='lines',
                    name=exchange,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '时间: %{x}<br>' +
                                  '延迟: %{y:.1f} ms<extra></extra>'
                ))
            
            fig.update_layout(
                title="24小时网络延迟趋势",
                xaxis_title="时间",
                yaxis_title="延迟 (ms)",
                height=400,
                hovermode='x unified',
                font=dict(size=12),
                title_font_size=16
            )
            
            return fig
            
        except Exception as e:
            st.error(f"渲染趋势图时出错: {e}")
            return go.Figure()
    
    @staticmethod
    def render_network_quality_gauge(avg_latency: float) -> go.Figure:
        """渲染网络质量仪表盘"""
        try:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=avg_latency,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "平均网络延迟 (ms)"},
                delta={'reference': NetworkConfig.EXCELLENT_THRESHOLD},
                gauge={
                    'axis': {'range': [None, 200]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, NetworkConfig.EXCELLENT_THRESHOLD], 'color': "lightgreen"},
                        {'range': [NetworkConfig.EXCELLENT_THRESHOLD, NetworkConfig.GOOD_THRESHOLD], 'color': "yellow"},
                        {'range': [NetworkConfig.GOOD_THRESHOLD, NetworkConfig.FAIR_THRESHOLD], 'color': "orange"},
                        {'range': [NetworkConfig.FAIR_THRESHOLD, 200], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': NetworkConfig.GOOD_THRESHOLD
                    }
                }
            ))
            
            fig.update_layout(height=300)
            return fig
            
        except Exception as e:
            st.error(f"渲染仪表盘时出错: {e}")
            return go.Figure()

class NetworkAnalyzer:
    """网络分析器"""
    
    @staticmethod
    def calculate_exchange_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """计算交易所指标"""
        try:
            metrics = df.groupby('exchange').agg({
                'latency': 'mean',
                'packet_loss': 'mean',
                'jitter': 'mean'
            }).round(2)
            
            metrics['status'] = metrics['latency'].apply(
                lambda x: "🟢 优秀" if x < NetworkConfig.EXCELLENT_THRESHOLD 
                else "🟡 良好" if x < NetworkConfig.GOOD_THRESHOLD 
                else "🟠 一般" if x < NetworkConfig.FAIR_THRESHOLD 
                else "🔴 较差"
            )
            
            metrics = metrics.reset_index()
            metrics.columns = ['交易所', '平均延迟(ms)', '丢包率(%)', '抖动(ms)', '状态']
            
            return metrics
            
        except Exception as e:
            st.error(f"计算指标时出错: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def generate_warnings(df: pd.DataFrame) -> List[str]:
        """生成网络预警"""
        warnings = []
        
        try:
            avg_latency = df['latency'].mean()
            max_latency = df['latency'].max()
            avg_packet_loss = df['packet_loss'].mean()
            
            if avg_latency > NetworkConfig.GOOD_THRESHOLD:
                warnings.append("🔴 整体网络延迟偏高")
            if max_latency > 200:
                warnings.append("🟠 部分交易所延迟异常")
            if avg_packet_loss > 1:
                warnings.append("🟡 网络丢包率偏高")
            
            if not warnings:
                warnings.append("🟢 网络状态良好")
                
        except Exception as e:
            st.error(f"生成预警时出错: {e}")
            warnings.append("⚠️ 预警系统异常")
        
        return warnings

def render_overview_metrics(df: pd.DataFrame) -> None:
    """渲染概览指标"""
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        avg_latency = df['latency'].mean()
        min_latency = df['latency'].min()
        max_latency = df['latency'].max()
        avg_packet_loss = df['packet_loss'].mean()
        
        with col1:
            st.metric(
                "平均延迟",
                f"{avg_latency:.1f} ms",
                delta=f"{random.uniform(-5, 5):.1f} ms"
            )
        
        with col2:
            st.metric(
                "最低延迟",
                f"{min_latency:.1f} ms",
                delta="优秀" if min_latency < 30 else "良好"
            )
        
        with col3:
            st.metric(
                "最高延迟",
                f"{max_latency:.1f} ms",
                delta="警告" if max_latency > 150 else "正常"
            )
        
        with col4:
            st.metric(
                "平均丢包率",
                f"{avg_packet_loss:.2f}%",
                delta="正常" if avg_packet_loss < 1 else "异常"
            )
            
    except Exception as e:
        st.error(f"渲染概览指标时出错: {e}")

def render_network_monitor() -> None:
    """渲染完整的网络监控界面"""
    try:
        st.header("🌐 网络延迟监控系统")
        
        # 生成数据
        df_current = NetworkDataGenerator.generate_current_latency()
        df_historical = NetworkDataGenerator.generate_historical_latency()
        
        if df_current.empty:
            st.error("无法获取网络数据")
            return
        
        # 实时状态概览
        render_overview_metrics(df_current)
        st.markdown("---")
        
        # 网络质量仪表盘和延迟热力图
        col1, col2 = st.columns([1, 2])
        
        with col1:
            avg_latency = df_current['latency'].mean()
            gauge_fig = NetworkChartRenderer.render_network_quality_gauge(avg_latency)
            st.plotly_chart(gauge_fig, use_container_width=True)
        
        with col2:
            heatmap_fig = NetworkChartRenderer.render_latency_heatmap(df_current)
            st.plotly_chart(heatmap_fig, use_container_width=True)
        
        # 历史趋势分析
        if not df_historical.empty:
            st.subheader("📈 延迟趋势分析")
            trend_fig = NetworkChartRenderer.render_latency_trend(df_historical)
            st.plotly_chart(trend_fig, use_container_width=True)
        
        # API状态详情和预警
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 交易所API状态详情")
            status_df = NetworkAnalyzer.calculate_exchange_metrics(df_current)
            if not status_df.empty:
                st.dataframe(status_df, use_container_width=True)
        
        with col2:
            st.subheader("⚠️ 网络预警")
            warnings = NetworkAnalyzer.generate_warnings(df_current)
            for warning in warnings:
                st.markdown(warning)
            
            st.markdown("---")
            st.subheader("💡 优化建议")
            st.info("""
            **当前建议:**
            
            • 优先使用亚洲节点
            • 避免高延迟交易所
            • 启用网络加速
            • 监控异常波动
            """)
        
        # 实时刷新控制
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 刷新数据"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("自动刷新", value=False)
        
        with col3:
            if auto_refresh:
                st.info("每30秒自动刷新数据")
                time.sleep(30)
                st.rerun()
        
        st.markdown(f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
    except Exception as e:
        st.error(f"网络监控系统出错: {e}")
        st.info("请刷新页面重试")