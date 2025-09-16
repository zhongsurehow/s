"""
专业交易界面组件模块
包含专业交易界面的所有渲染函数
"""

import streamlit as st
from typing import List, Any

from ..ui.professional_trading import trading_interface


def render_professional_trading_interface(engine, providers: List):
    """渲染专业交易界面"""
    st.title("💼 专业交易界面")
    st.markdown("---")
    
    # 渲染布局选择器
    selected_layout = trading_interface.render_layout_selector()
    
    # 渲染布局自定义器
    trading_interface.render_layout_customizer()
    
    # 渲染主交易界面
    trading_interface.render_trading_interface(selected_layout, engine, providers)
    
    # 处理快捷操作的弹窗
    _handle_quick_actions()


def _handle_quick_actions():
    """处理快捷操作弹窗"""
    _handle_quick_analysis()
    _handle_arbitrage_search()
    _handle_risk_check()
    _handle_technical_analysis()


def _handle_quick_analysis():
    """处理快速分析弹窗"""
    if st.session_state.get('show_quick_analysis', False):
        with st.expander("📊 快速分析", expanded=True):
            st.write("### 市场快速分析")
            
            # 生成模拟分析数据
            analysis_data = {
                '市场趋势': '上涨',
                '波动率': '中等',
                '成交量': '活跃',
                '技术指标': 'RSI: 65, MACD: 正向',
                '支撑位': '$42,800',
                '阻力位': '$44,200'
            }
            
            for key, value in analysis_data.items():
                st.metric(key, value)
            
            if st.button("关闭分析"):
                st.session_state.show_quick_analysis = False
                st.rerun()


def _handle_arbitrage_search():
    """处理套利机会搜索弹窗"""
    if st.session_state.get('show_arbitrage_search', False):
        with st.expander("🎯 套利机会搜索", expanded=True):
            st.write("### 实时套利机会")
            st.info("正在搜索套利机会...")
            
            # 模拟套利机会
            opportunities = [
                {'交易对': 'BTC/USDT', '交易所A': 'Binance', '交易所B': 'OKX', '价差': '0.15%', '利润': '$65'},
                {'交易对': 'ETH/USDT', '交易所A': 'Huobi', '交易所B': 'Binance', '价差': '0.08%', '利润': '$23'}
            ]
            
            for opp in opportunities:
                st.write(f"**{opp['交易对']}**: {opp['交易所A']} vs {opp['交易所B']} - 价差: {opp['价差']}, 预期利润: {opp['利润']}")
            
            if st.button("关闭搜索"):
                st.session_state.show_arbitrage_search = False
                st.rerun()


def _handle_risk_check():
    """处理风险检查弹窗"""
    if st.session_state.get('show_risk_check', False):
        with st.expander("⚠️ 风险检查", expanded=True):
            st.write("### 风险评估报告")
            
            risk_metrics = {
                '总体风险等级': '中等',
                '仓位风险': '低',
                '流动性风险': '低',
                '市场风险': '中等',
                'VaR (1日)': '$1,250',
                '最大回撤': '3.2%'
            }
            
            for metric, value in risk_metrics.items():
                st.metric(metric, value)
            
            if st.button("关闭风险检查"):
                st.session_state.show_risk_check = False
                st.rerun()


def _handle_technical_analysis():
    """处理技术分析弹窗"""
    if st.session_state.get('show_technical_analysis', False):
        with st.expander("📈 技术分析工具", expanded=True):
            st.write("### 技术分析")
            
            # 技术指标选择
            indicators = st.multiselect(
                "选择技术指标",
                ["RSI", "MACD", "布林带", "移动平均线", "成交量"],
                default=["RSI", "MACD"]
            )
            
            st.write("**当前技术指标状态:**")
            for indicator in indicators:
                if indicator == "RSI":
                    st.write(f"• RSI(14): 65.2 - 中性偏多")
                elif indicator == "MACD":
                    st.write(f"• MACD: 正向交叉 - 买入信号")
                elif indicator == "布林带":
                    st.write(f"• 布林带: 价格接近上轨 - 超买区域")
                elif indicator == "移动平均线":
                    st.write(f"• MA(20): 上升趋势 - 多头排列")
                elif indicator == "成交量":
                    st.write(f"• 成交量: 放量上涨 - 趋势确认")
            
            if st.button("关闭技术分析"):
                st.session_state.show_technical_analysis = False
                st.rerun()