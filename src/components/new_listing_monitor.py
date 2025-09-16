"""
新货币上市监控组件
监控八大交易所的新货币上市情况，及时提醒用户
"""

import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

from providers.real_data_service import real_data_service

class NewListingMonitor:
    """新货币上市监控器"""
    
    def __init__(self):
        self.target_exchanges = [
            'binance', 'okx', 'bybit', 'kucoin', 
            'gate', 'mexc', 'bitget', 'huobi'
        ]
    
    @st.cache_data(ttl=300)  # 缓存5分钟
    def get_new_listings(_self) -> List[Dict[str, Any]]:
        """获取新上市货币"""
        try:
            # 使用异步函数获取新上市检测
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_listings = loop.run_until_complete(
                real_data_service.detect_new_listings()
            )
            loop.close()
            
            return new_listings
            
        except Exception as e:
            st.error(f"检测新上市失败: {e}")
            return []
    
    def render_new_listing_alerts(self) -> None:
        """渲染新上市提醒"""
        st.subheader("🚨 新货币上市提醒")
        
        new_listings = self.get_new_listings()
        
        if new_listings:
            # 显示提醒数量
            st.success(f"发现 {len(new_listings)} 个新上市货币！")
            
            # 创建数据表格
            df = pd.DataFrame(new_listings)
            
            # 格式化显示
            if not df.empty:
                df['detected_at'] = pd.to_datetime(df['detected_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df['price'] = df['price'].apply(lambda x: f"${x:.6f}")
                df['volume'] = df['volume'].apply(lambda x: f"{x:,.0f}")
                df['涨跌24h'] = df['涨跌24h'].apply(lambda x: f"{x:+.2f}%")
                
                # 重命名列
                df_display = df.rename(columns={
                    'symbol': '交易对',
                    'exchange': '交易所',
                    'price': '当前价格',
                    'volume': '24h交易量',
                    '涨跌24h': '24h涨跌',
                    'detected_at': '检测时间'
                })
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )
                
                # 显示详细信息
                with st.expander("📊 新上市详细分析"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 按交易所分布
                        exchange_counts = df['exchange'].value_counts()
                        fig_exchange = px.pie(
                            values=exchange_counts.values,
                            names=exchange_counts.index,
                            title="新上市货币按交易所分布"
                        )
                        st.plotly_chart(fig_exchange, use_container_width=True)
                    
                    with col2:
                        # 交易量分布
                        fig_volume = px.bar(
                            x=df['symbol'],
                            y=df['volume'].str.replace(',', '').str.replace('$', '').astype(float),
                            title="新上市货币24h交易量",
                            labels={'x': '交易对', 'y': '交易量'}
                        )
                        fig_volume.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_volume, use_container_width=True)
                
                # 提醒设置
                with st.expander("⚙️ 提醒设置"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        min_volume = st.number_input(
                            "最小交易量阈值",
                            min_value=0,
                            value=1000,
                            help="只提醒交易量大于此值的新上市货币"
                        )
                    
                    with col2:
                        alert_exchanges = st.multiselect(
                            "监控交易所",
                            options=self.target_exchanges,
                            default=self.target_exchanges,
                            help="选择要监控的交易所"
                        )
                    
                    with col3:
                        auto_refresh = st.checkbox(
                            "自动刷新",
                            value=True,
                            help="每5分钟自动检查新上市"
                        )
                    
                    if st.button("💾 保存设置"):
                        st.success("设置已保存！")
        else:
            st.info("暂未发现新上市货币")
            
            # 显示监控状态
            with st.expander("📡 监控状态"):
                st.write("**监控的交易所:**")
                for exchange in self.target_exchanges:
                    st.write(f"• {exchange.upper()}")
                
                st.write("**检查频率:** 每5分钟")
                st.write("**最后检查时间:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    def render_listing_history(self) -> None:
        """渲染上市历史"""
        st.subheader("📈 近期上市历史")
        
        # 这里可以扩展为显示历史上市数据
        # 目前显示模拟的历史数据
        
        # 创建示例历史数据
        history_data = [
            {
                'date': '2024-01-15',
                'symbol': 'NEW1/USDT',
                'exchange': 'binance',
                'initial_price': 0.001234,
                'current_price': 0.002456,
                'change': '+99.35%'
            },
            {
                'date': '2024-01-14',
                'symbol': 'NEW2/USDT',
                'exchange': 'okx',
                'initial_price': 0.000567,
                'current_price': 0.000234,
                'change': '-58.73%'
            }
        ]
        
        if history_data:
            df_history = pd.DataFrame(history_data)
            df_history = df_history.rename(columns={
                'date': '上市日期',
                'symbol': '交易对',
                'exchange': '交易所',
                'initial_price': '初始价格',
                'current_price': '当前价格',
                'change': '涨跌幅'
            })
            
            st.dataframe(
                df_history,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("暂无历史上市数据")
    
    def render_market_impact_analysis(self) -> None:
        """渲染市场影响分析"""
        st.subheader("🎯 市场影响分析")
        
        new_listings = self.get_new_listings()
        
        if new_listings:
            # 分析新上市对市场的影响
            total_volume = sum(
                float(listing['volume']) for listing in new_listings
            )
            
            avg_change = sum(
                float(listing['涨跌24h']) for listing in new_listings
            ) / len(new_listings)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "新上市总交易量",
                    f"{total_volume:,.0f}",
                    help="所有新上市货币的24h总交易量"
                )
            
            with col2:
                st.metric(
                    "平均涨跌幅",
                    f"{avg_change:+.2f}%",
                    delta=f"{avg_change:+.2f}%"
                )
            
            with col3:
                st.metric(
                    "活跃交易所",
                    len(set(listing['exchange'] for listing in new_listings)),
                    help="有新上市的交易所数量"
                )
            
            # 风险提示
            st.warning("""
            ⚠️ **新上市货币投资风险提示:**
            - 新上市货币价格波动极大，存在高风险
            - 建议充分研究项目基本面后再做投资决策
            - 注意流动性风险和市场操纵风险
            - 建议小额试水，切勿重仓投入
            """)
        else:
            st.info("暂无新上市数据进行分析")

def render_new_listing_monitor():
    """渲染新货币上市监控页面"""
    monitor = NewListingMonitor()
    
    # 页面标题
    st.title("🔍 新货币上市监控")
    st.markdown("---")
    
    # 主要功能标签页
    tab1, tab2, tab3 = st.tabs(["🚨 实时提醒", "📈 上市历史", "🎯 市场分析"])
    
    with tab1:
        monitor.render_new_listing_alerts()
    
    with tab2:
        monitor.render_listing_history()
    
    with tab3:
        monitor.render_market_impact_analysis()
    
    # 自动刷新功能
    if st.button("🔄 手动刷新"):
        st.cache_data.clear()
        st.rerun()