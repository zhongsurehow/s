"""
套利机会页面 - 专业套利交易系统
提供实时套利机会分析、执行监控、风险评估和网络监控功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import random
import sys
import os
from typing import Dict, List, Tuple, Optional

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from components.execution_monitor import render_execution_monitor, render_risk_dashboard
from components.network_monitor import render_network_monitor
from components.main_console import render_main_console
from providers.real_data_service import real_data_service
import asyncio

# 配置常量
CURRENCIES = [
    "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", "SHIB",
    "AVAX", "LTC", "UNI", "LINK", "ATOM", "XLM", "BCH", "ALGO", "VET", "ICP",
    "FIL", "TRX", "ETC", "THETA", "XMR", "HBAR", "NEAR", "FLOW", "EGLD", "XTZ",
    "MANA", "SAND", "AXS", "CHZ", "ENJ", "BAT", "ZIL", "HOT", "IOTA", "QTUM",
    "OMG", "ZRX", "COMP", "MKR", "SNX", "SUSHI", "YFI", "AAVE", "CRV", "1INCH",
    "RUNE", "LUNA", "UST", "KLAY", "FTT", "HNT", "WAVES", "KSM", "DASH", "ZEC",
    "DCR", "RVN", "DGB", "SC", "BTG", "NANO", "ICX", "ONT", "LSK", "STEEM",
    "ARK", "STRAX", "NEM", "XEM", "MAID", "STORJ", "SIA", "GNT", "REP", "ANT",
    "MODE", "TAVA", "SUIAI", "LIVE", "AIC", "GEL", "PEPE", "FLOKI", "BONK", "WIF",
    "BOME", "SLERF", "MYRO", "POPCAT", "MOODENG", "GOAT", "PNUT", "ACT", "NEIRO", "TURBO"
]

EXCHANGES = ["Binance", "OKX", "Huobi", "KuCoin", "Gate.io", "Bybit", "Coinbase", "Kraken"]

NETWORK_FEATURES = {
    'ETH': {'avg_latency': 60, 'fee_level': '高', 'success_rate': 98},
    'BSC': {'avg_latency': 15, 'fee_level': '低', 'success_rate': 99},
    'TRX': {'avg_latency': 10, 'fee_level': '极低', 'success_rate': 97},
    'MATIC': {'avg_latency': 8, 'fee_level': '极低', 'success_rate': 99},
    'AVAX': {'avg_latency': 12, 'fee_level': '低', 'success_rate': 98},
    'SOL': {'avg_latency': 5, 'fee_level': '极低', 'success_rate': 96},
    'ATOM': {'avg_latency': 20, 'fee_level': '中', 'success_rate': 97},
    'DOT': {'avg_latency': 25, 'fee_level': '中', 'success_rate': 98}
}

QUICK_FILTERS = {
    "全部机会": {},
    "高收益低风险": {"min_profit": 2.0, "risk_level": "低风险", "executable_only": True},
    "快速执行": {"max_latency": 5, "difficulty": "简单", "executable_only": True},
    "高成功率": {"min_success_rate": 95, "executable_only": True},
    "简单操作": {"difficulty": "简单", "liquidity": "高", "executable_only": True}
}


def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="套利机会",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def generate_arbitrage_opportunity(currency: str, buy_exchange: str, sell_exchange: str) -> Dict:
    """生成单个套利机会数据"""
    # 基础价格和价差
    base_price = random.uniform(0.1, 50000)
    price_diff = random.uniform(0.1, 4.0)
    
    # 网络选择
    networks = list(NETWORK_FEATURES.keys())
    withdraw_network = random.choice(networks)
    deposit_network = random.choice(networks)
    unified_network = withdraw_network if withdraw_network == deposit_network else "-"
    
    # 计算专业指标
    network_info = NETWORK_FEATURES.get(withdraw_network, NETWORK_FEATURES['ETH'])
    
    execution_difficulty = random.choices(
        ["🟢 简单", "🟡 中等", "🔴 困难"],
        weights=[0.4, 0.4, 0.2]
    )[0]
    
    success_rate = max(70, network_info['success_rate'] + random.gauss(0, 5))
    network_latency = max(1, network_info['avg_latency'] + random.gauss(0, 10))
    estimated_time = network_latency + random.uniform(30, 180)
    
    liquidity = random.choices(
        ["🟢 高", "🟡 中", "🔴 低"],
        weights=[0.3, 0.5, 0.2]
    )[0]
    
    risk_level = random.choices(
        ["🟢 低风险", "🟡 中风险", "🔴 高风险"],
        weights=[0.3, 0.5, 0.2]
    )[0]
    
    return {
        "币种": currency,
        "买入平台": buy_exchange,
        "卖出平台": sell_exchange,
        "买入价格": f"${base_price:.4f}",
        "卖出价格": f"${base_price * (1 + price_diff/100):.4f}",
        "价格差": f"{price_diff:.2f}%",
        "提现网络": withdraw_network,
        "充值网络": deposit_network,
        "充提合一": unified_network,
        "执行难度": execution_difficulty,
        "成功率": f"{success_rate:.1f}%",
        "网络延迟": f"{network_latency:.0f}秒",
        "预估时间": f"{estimated_time:.0f}秒",
        "流动性": liquidity,
        "风险等级": risk_level,
        "手续费等级": network_info['fee_level']
    }


@st.cache_data(ttl=60)
def generate_arbitrage_data() -> pd.DataFrame:
    """生成完整的套利数据"""
    data = []
    
    try:
        # 生成套利机会
        for _ in range(200):  # 生成200个机会
            currency = random.choice(CURRENCIES)
            buy_exchange = random.choice(EXCHANGES)
            sell_exchange = random.choice([ex for ex in EXCHANGES if ex != buy_exchange])
            
            opportunity = generate_arbitrage_opportunity(currency, buy_exchange, sell_exchange)
            data.append(opportunity)
        
        df = pd.DataFrame(data)
        
        # 确保数据完整性
        if len(df) == 0:
            st.error("数据生成失败，请刷新页面重试")
            return pd.DataFrame()
            
        return df
        
    except Exception as e:
        st.error(f"数据生成错误: {str(e)}")
        return pd.DataFrame()


def apply_quick_filter(df: pd.DataFrame, filter_name: str) -> pd.DataFrame:
    """应用快速筛选"""
    if filter_name not in QUICK_FILTERS:
        return df
    
    filter_config = QUICK_FILTERS[filter_name]
    filtered_df = df.copy()
    
    # 转换数值列
    filtered_df["价格差_数值"] = filtered_df["价格差"].str.rstrip("%").astype(float)
    filtered_df["成功率_数值"] = filtered_df["成功率"].str.rstrip("%").astype(float)
    filtered_df["网络延迟_数值"] = filtered_df["网络延迟"].str.rstrip("秒").astype(float)
    
    # 应用筛选条件
    if "min_profit" in filter_config:
        filtered_df = filtered_df[filtered_df["价格差_数值"] >= filter_config["min_profit"]]
    
    if "risk_level" in filter_config:
        filtered_df = filtered_df[filtered_df["风险等级"].str.contains(filter_config["risk_level"])]
    
    if "max_latency" in filter_config:
        filtered_df = filtered_df[filtered_df["网络延迟_数值"] <= filter_config["max_latency"]]
    
    if "difficulty" in filter_config:
        filtered_df = filtered_df[filtered_df["执行难度"].str.contains(filter_config["difficulty"])]
    
    if "min_success_rate" in filter_config:
        filtered_df = filtered_df[filtered_df["成功率_数值"] >= filter_config["min_success_rate"]]
    
    if "liquidity" in filter_config:
        filtered_df = filtered_df[filtered_df["流动性"].str.contains(filter_config["liquidity"])]
    
    if filter_config.get("executable_only", False):
        filtered_df = filtered_df[filtered_df["充提合一"] != "-"]
    
    return filtered_df


def render_sidebar_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """渲染侧边栏筛选器"""
    st.sidebar.header("🔍 智能筛选")
    
    # 快速筛选
    st.sidebar.subheader("⚡ 快速筛选")
    quick_filter = st.sidebar.selectbox(
        "选择预设筛选",
        list(QUICK_FILTERS.keys()),
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # 基础筛选
    st.sidebar.subheader("📊 基础条件")
    
    min_diff = st.sidebar.slider("最小价格差 (%)", 0.0, 5.0, 0.0, 0.1)
    max_diff = st.sidebar.slider("最大价格差 (%)", 0.0, 5.0, 5.0, 0.1)
    
    exchanges = sorted(list(set(df["买入平台"].tolist() + df["卖出平台"].tolist())))
    selected_exchanges = st.sidebar.multiselect("选择交易所", exchanges, default=exchanges)
    
    networks = sorted(df["充提合一"].unique().tolist())
    selected_networks = st.sidebar.multiselect("选择网络", networks, default=networks)
    
    search_currency = st.sidebar.text_input("搜索币种", "").upper()
    
    st.sidebar.markdown("---")
    
    # 专业筛选
    st.sidebar.subheader("🎯 专业筛选")
    
    difficulty_options = ["🟢 简单", "🟡 中等", "🔴 困难"]
    selected_difficulty = st.sidebar.multiselect("执行难度", difficulty_options, default=difficulty_options)
    
    min_success_rate = st.sidebar.slider("最低成功率 (%)", 0, 100, 0, 5)
    
    risk_options = ["🟢 低风险", "🟡 中风险", "🔴 高风险"]
    selected_risk = st.sidebar.multiselect("风险等级", risk_options, default=risk_options)
    
    liquidity_options = ["🟢 高", "🟡 中", "🔴 低"]
    selected_liquidity = st.sidebar.multiselect("流动性要求", liquidity_options, default=liquidity_options)
    
    max_latency = st.sidebar.slider("最大网络延迟 (秒)", 1, 60, 60, 1)
    
    only_executable = st.sidebar.checkbox("只显示可执行机会", value=False)
    
    # 应用筛选
    filtered_df = apply_quick_filter(df, quick_filter)
    
    # 应用基础筛选
    if "价格差_数值" not in filtered_df.columns:
        filtered_df["价格差_数值"] = filtered_df["价格差"].str.rstrip("%").astype(float)
        filtered_df["成功率_数值"] = filtered_df["成功率"].str.rstrip("%").astype(float)
        filtered_df["网络延迟_数值"] = filtered_df["网络延迟"].str.rstrip("秒").astype(float)
    
    filtered_df = filtered_df[
        (filtered_df["价格差_数值"] >= min_diff) &
        (filtered_df["价格差_数值"] <= max_diff) &
        (filtered_df["买入平台"].isin(selected_exchanges)) &
        (filtered_df["卖出平台"].isin(selected_exchanges)) &
        (filtered_df["充提合一"].isin(selected_networks))
    ]
    
    # 应用专业筛选
    if search_currency:
        filtered_df = filtered_df[filtered_df["币种"].str.contains(search_currency)]
    
    if selected_difficulty:
        filtered_df = filtered_df[filtered_df["执行难度"].isin(selected_difficulty)]
    
    if min_success_rate > 0:
        filtered_df = filtered_df[filtered_df["成功率_数值"] >= min_success_rate]
    
    if selected_risk:
        filtered_df = filtered_df[filtered_df["风险等级"].isin(selected_risk)]
    
    if selected_liquidity:
        filtered_df = filtered_df[filtered_df["流动性"].isin(selected_liquidity)]
    
    if max_latency < 60:
        filtered_df = filtered_df[filtered_df["网络延迟_数值"] <= max_latency]
    
    if only_executable:
        filtered_df = filtered_df[filtered_df["充提合一"] != "-"]
    
    filter_info = {
        "quick_filter": quick_filter,
        "min_diff": min_diff,
        "max_diff": max_diff,
        "selected_exchanges": selected_exchanges,
        "search_currency": search_currency
    }
    
    return filtered_df, filter_info


def calculate_metrics(df: pd.DataFrame) -> Dict:
    """计算统计指标"""
    if len(df) == 0:
        return {
            "total_opportunities": 0,
            "avg_diff": 0,
            "max_diff": 0,
            "high_profit": 0,
            "executable": 0,
            "easy_ops": 0,
            "high_success": 0,
            "low_risk": 0,
            "high_liquidity": 0,
            "fast_networks": 0
        }
    
    price_diff_values = df["价格差_数值"] if "价格差_数值" in df.columns else df["价格差"].str.rstrip("%").astype(float)
    success_rate_values = df["成功率_数值"] if "成功率_数值" in df.columns else df["成功率"].str.rstrip("%").astype(float)
    latency_values = df["网络延迟_数值"] if "网络延迟_数值" in df.columns else df["网络延迟"].str.rstrip("秒").astype(float)
    
    return {
        "total_opportunities": len(df),
        "avg_diff": price_diff_values.mean(),
        "max_diff": price_diff_values.max(),
        "high_profit": len(df[price_diff_values > 2.0]),
        "executable": len(df[df["充提合一"] != "-"]),
        "easy_ops": len(df[df["执行难度"].str.contains("简单")]),
        "high_success": len(df[success_rate_values >= 95]),
        "low_risk": len(df[df["风险等级"].str.contains("低风险")]),
        "high_liquidity": len(df[df["流动性"].str.contains("高")]),
        "fast_networks": len(df[latency_values <= 5])
    }


def render_metrics_overview(metrics: Dict):
    """渲染指标概览"""
    st.subheader("📊 实时套利概览")
    
    # 第一行指标
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("总套利机会", metrics["total_opportunities"])
    
    with col2:
        st.metric("平均价格差", f"{metrics['avg_diff']:.2f}%")
    
    with col3:
        st.metric("最大价格差", f"{metrics['max_diff']:.2f}%")
    
    with col4:
        st.metric("高收益机会", f"{metrics['high_profit']}/{metrics['total_opportunities']}")
    
    with col5:
        st.metric("可执行机会", f"{metrics['executable']}/{metrics['total_opportunities']}")
    
    # 第二行专业指标
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("🟢 简单执行", metrics["easy_ops"])
    
    with col2:
        st.metric("高成功率(≥95%)", metrics["high_success"])
    
    with col3:
        st.metric("🟢 低风险", metrics["low_risk"])
    
    with col4:
        st.metric("🟢 高流动性", metrics["high_liquidity"])
    
    with col5:
        st.metric("快速网络(≤5s)", metrics["fast_networks"])


def highlight_rows(row):
    """为表格行添加颜色编码"""
    try:
        price_diff = float(row["价格差"].rstrip("%"))
        risk_level = row["风险等级"]
        difficulty = row["执行难度"]
        executable = row["充提合一"]
        
        if executable == "-":
            return ['background-color: #f8f9fa'] * len(row)  # 灰色
        elif price_diff >= 2.0 and "低风险" in risk_level and "简单" in difficulty:
            return ['background-color: #d4edda'] * len(row)  # 绿色
        elif price_diff < 1.0 or "高风险" in risk_level or "困难" in difficulty:
            return ['background-color: #f8d7da'] * len(row)  # 红色
        else:
            return ['background-color: #fff3cd'] * len(row)  # 黄色
    except:
        return [''] * len(row)


def render_opportunities_table(df: pd.DataFrame):
    """渲染套利机会表格"""
    if len(df) == 0:
        st.warning("没有找到符合条件的套利机会，请调整筛选条件。")
        return
    
    st.subheader(f"套利机会列表 ({len(df)} 个机会)")
    
    # 颜色说明
    st.markdown("""
    **颜色说明：**
    - 🟢 绿色：高收益 + 低风险 + 简单执行
    - 🟡 黄色：中等收益或中等风险
    - 🔴 红色：低收益或高风险或困难执行
    - ⚫ 灰色：网络不匹配，无法执行
    """)
    
    # 排序并清理数据
    df_sorted = df.sort_values("价格差_数值", ascending=False) if "价格差_数值" in df.columns else df
    df_display = df_sorted.drop(columns=["价格差_数值", "成功率_数值", "网络延迟_数值"], errors='ignore')
    
    # 应用样式并显示表格
    styled_df = df_display.style.apply(highlight_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # 下载按钮
    csv = df_display.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 下载套利机会数据",
        data=csv,
        file_name=f"arbitrage_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def render_arbitrage_explanation():
    """渲染套利说明"""
    with st.expander("📚 套利操作说明", expanded=False):
        st.markdown("""
        ### 🔗 网络概念解释
        
        **🔗 提现网络**
        提现网络是指从买入平台提取加密货币时使用的区块链网络。
        
        **📥 充值网络**
        充值网络是指向卖出平台充值加密货币时支持的区块链网络。
        
        **✅ 充提合一**
        充提合一表示提现网络和充值网络完全匹配，可以直接进行套利操作。
        
        ### 📋 完整套利流程
        
        1. **选择机会** → 找到充提合一显示具体网络的套利机会
        2. **买入** → 在买入平台购买加密货币
        3. **提现** → 使用指定的提现网络提取到个人钱包
        4. **充值** → 使用相同网络充值到卖出平台
        5. **卖出** → 在卖出平台以更高价格卖出
        6. **获利** → 扣除手续费后获得套利收益
        
        ### ⚠️ 风险提示
        
        - 数据仅供参考，实际交易前请验证价格
        - 考虑交易手续费、提币费用和时间成本
        - 注意市场波动风险和流动性风险
        - 建议小额测试后再进行大额套利
        """)


def render_arbitrage_opportunities():
    """渲染套利机会主页面"""
    try:
        # 获取数据
        df = generate_arbitrage_data()
        
        if df.empty:
            st.warning("⚠️ 数据加载失败，请点击刷新数据按钮重试")
            return
        
        st.success(f"✅ 成功加载 {len(df)} 个套利机会")
        
        # 渲染筛选器
        filtered_df, filter_info = render_sidebar_filters(df)
        
        # 计算指标
        metrics = calculate_metrics(filtered_df)
        
        # 渲染指标概览
        render_metrics_overview(metrics)
        
        st.markdown("---")
        
        # 渲染机会表格
        render_opportunities_table(filtered_df)
        
        # 渲染说明
        render_arbitrage_explanation()
        
        # 刷新按钮
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 刷新数据"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            st.markdown(f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            
    except Exception as e:
        st.error(f"❌ 页面渲染错误: {str(e)}")
        st.info("请尝试刷新页面或联系技术支持")


def main():
    """主函数"""
    st.title("💰 专业套利交易系统")
    st.markdown("---")
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 主控制台", 
        "🔍 套利机会", 
        "⚡ 执行监控", 
        "🛡️ 风险控制", 
        "🌐 网络监控"
    ])
    
    with tab1:
        render_main_console()
    
    with tab2:
        render_arbitrage_opportunities()
    
    with tab3:
        render_execution_monitor()
    
    with tab4:
        render_risk_dashboard()
    
    with tab5:
        render_network_monitor()


if __name__ == "__main__":
    main()