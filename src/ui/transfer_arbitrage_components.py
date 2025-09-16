"""
转账路径规划和套利机会组件模块
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
from ..utils.async_utils import safe_run_async


def render_transfer_path_planner(transfer_path_planner):
    """渲染转账路径规划器界面"""
    st.subheader("🛣️ 转账路径规划器")
    
    # 控制面板
    _render_transfer_control_panel(transfer_path_planner)
    
    # 规划按钮和结果显示
    _handle_transfer_planning(transfer_path_planner)
    
    # 功能说明
    _render_transfer_help()


def _render_transfer_control_panel(transfer_path_planner):
    """渲染转账控制面板"""
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 源平台选择
            source_platforms = list(transfer_path_planner.platforms.keys())
            from_platform = st.selectbox(
                "源平台",
                source_platforms,
                key="transfer_from_platform"
            )
        
        with col2:
            # 目标平台选择
            target_platforms = [p for p in source_platforms if p != from_platform]
            to_platform = st.selectbox(
                "目标平台",
                target_platforms,
                key="transfer_to_platform"
            )
        
        with col3:
            # 代币选择
            if from_platform and to_platform:
                from_tokens = transfer_path_planner.platforms[from_platform].get('supported_tokens', [])
                to_tokens = transfer_path_planner.platforms[to_platform].get('supported_tokens', [])
                common_tokens = list(set(from_tokens) & set(to_tokens))
                
                token = st.selectbox(
                    "转账代币",
                    common_tokens,
                    key="transfer_token"
                )
            else:
                token = st.selectbox("转账代币", [], key="transfer_token")
        
        with col4:
            # 转账金额
            amount = st.number_input(
                "转账金额",
                min_value=0.01,
                max_value=1000000.0,
                value=1000.0,
                step=100.0,
                key="transfer_amount"
            )


def _handle_transfer_planning(transfer_path_planner):
    """处理转账路径规划逻辑"""
    from_platform = st.session_state.get('transfer_from_platform')
    to_platform = st.session_state.get('transfer_to_platform')
    token = st.session_state.get('transfer_token')
    amount = st.session_state.get('transfer_amount', 0)
    
    # 规划按钮
    if st.button("🔍 规划转账路径", type="primary"):
        if from_platform and to_platform and token and amount > 0:
            with st.spinner("正在规划最优转账路径..."):
                try:
                    # 规划转账路径
                    paths = safe_run_async(
                        transfer_path_planner.plan_transfer_paths(
                            from_platform, to_platform, token, amount
                        )
                    )
                    
                    if paths:
                        _display_transfer_paths(paths, amount, token, transfer_path_planner)
                    else:
                        _display_no_paths_found()
                
                except Exception as e:
                    st.error(f"规划路径时发生错误: {str(e)}")
                    st.write("请检查网络连接或稍后重试")
        else:
            st.warning("请填写完整的转账信息")


def _display_transfer_paths(paths, amount, token, transfer_path_planner):
    """显示转账路径结果"""
    st.success(f"找到 {len(paths)} 条可用路径")
    
    # 路径概览
    comparison = transfer_path_planner.generate_path_comparison(paths)
    st.info(f"📊 {comparison['summary']}")
    
    # 路径详情
    st.subheader("📋 转账路径详情")
    
    for i, path in enumerate(paths[:5]):  # 显示前5条路径
        _render_path_details(path, i, amount, token)
    
    # 路径对比图表
    if len(paths) > 1:
        _render_path_comparison_charts(paths)
    
    # 实时监控和建议
    _render_path_monitoring_and_recommendations(paths, amount)


def _render_path_details(path, index, amount, token):
    """渲染单个路径的详细信息"""
    with st.expander(f"路径 {index+1}: {path.path_id} (效率分数: {path.efficiency_score:.1f})", 
                   expanded=(index == 0)):
        
        # 路径基本信息
        path_col1, path_col2, path_col3, path_col4 = st.columns(4)
        
        with path_col1:
            st.metric("总费用", f"${path.total_fee:.2f}")
        
        with path_col2:
            st.metric("预计时间", f"{path.total_time} 分钟")
        
        with path_col3:
            st.metric("成功率", f"{path.success_rate*100:.1f}%")
        
        with path_col4:
            risk_color = {
                "低": "🟢",
                "中": "🟡", 
                "高": "🟠",
                "极高": "🔴"
            }.get(path.risk_level, "⚪")
            st.metric("风险等级", f"{risk_color} {path.risk_level}")
        
        # 转账步骤
        st.write("**转账步骤:**")
        
        steps_data = []
        for step in path.steps:
            steps_data.append({
                "步骤": step.step_id,
                "从": step.from_platform,
                "到": step.to_platform,
                "代币": f"{step.from_token} → {step.to_token}",
                "金额": f"{step.amount:.4f}",
                "费用": f"${step.estimated_fee:.2f}",
                "时间": f"{step.estimated_time}分钟",
                "类型": step.transfer_type.value,
                "桥/平台": step.bridge_name or "-"
            })
        
        steps_df = pd.DataFrame(steps_data)
        st.dataframe(steps_df, use_container_width=True)
        
        # 最终收益分析
        st.write("**收益分析:**")
        final_col1, final_col2, final_col3 = st.columns(3)
        
        with final_col1:
            st.metric("初始金额", f"{amount:.4f} {token}")
        
        with final_col2:
            st.metric("最终金额", f"{path.final_amount:.4f} {token}")
        
        with final_col3:
            loss_amount = amount - path.final_amount
            loss_percentage = (loss_amount / amount) * 100
            st.metric("损失", f"{loss_amount:.4f} {token}", 
                     delta=f"-{loss_percentage:.2f}%")


def _render_path_comparison_charts(paths):
    """渲染路径对比图表"""
    st.subheader("📊 路径对比分析")
    
    # 费用对比
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        fee_data = pd.DataFrame({
            '路径': [f"路径{i+1}" for i in range(len(paths[:5]))],
            '费用(USD)': [path.total_fee for path in paths[:5]]
        })
        
        fig_fee = px.bar(
            fee_data, 
            x='路径', 
            y='费用(USD)',
            title="转账费用对比",
            color='费用(USD)',
            color_continuous_scale='Reds'
        )
        fig_fee.update_layout(height=400)
        st.plotly_chart(fig_fee, use_container_width=True, key="transfer_fee_chart")
    
    with chart_col2:
        time_data = pd.DataFrame({
            '路径': [f"路径{i+1}" for i in range(len(paths[:5]))],
            '时间(分钟)': [path.total_time for path in paths[:5]]
        })
        
        fig_time = px.bar(
            time_data, 
            x='路径', 
            y='时间(分钟)',
            title="转账时间对比",
            color='时间(分钟)',
            color_continuous_scale='Blues'
        )
        fig_time.update_layout(height=400)
        st.plotly_chart(fig_time, use_container_width=True, key="transfer_time_chart")
    
    # 效率分数雷达图
    if len(paths) >= 3:
        _render_efficiency_radar_chart(paths)


def _render_efficiency_radar_chart(paths):
    """渲染效率雷达图"""
    radar_data = []
    for i, path in enumerate(paths[:3]):
        radar_data.append({
            '路径': f'路径{i+1}',
            '费用效率': max(0, 100 - (path.total_fee / 1000 * 100) * 10),
            '时间效率': max(0, 100 - (path.total_time / 60) * 20),
            '成功率': path.success_rate * 100,
            '综合效率': path.efficiency_score
        })
    
    radar_df = pd.DataFrame(radar_data)
    
    fig_radar = go.Figure()
    
    for _, row in radar_df.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row['费用效率'], row['时间效率'], row['成功率'], row['综合效率']],
            theta=['费用效率', '时间效率', '成功率', '综合效率'],
            fill='toself',
            name=row['路径']
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="路径效率对比雷达图",
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True, key="path_efficiency_radar_chart")


def _render_path_monitoring_and_recommendations(paths, amount):
    """渲染路径监控和建议"""
    # 实时监控
    st.subheader("📡 实时路径监控")
    
    monitor_col1, monitor_col2 = st.columns(2)
    
    with monitor_col1:
        if st.button("🔄 刷新路径状态"):
            st.rerun()
    
    with monitor_col2:
        auto_refresh = st.checkbox("自动刷新 (30秒)", key="path_auto_refresh")
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    # 路径建议
    st.subheader("💡 智能建议")
    
    best_path = paths[0]
    
    if best_path.risk_level == "低" and best_path.total_fee < amount * 0.01:
        st.success("✅ 推荐使用最优路径，风险低且费用合理")
    elif best_path.risk_level == "中":
        st.warning("⚠️ 建议谨慎使用，注意监控转账状态")
    else:
        st.error("❌ 不建议使用，风险较高，建议等待更好时机")
    
    # 费用优化建议
    if best_path.total_fee > amount * 0.02:
        st.info("💰 费用较高，建议考虑分批转账或等待网络拥堵缓解")
    
    # 时间优化建议
    if best_path.total_time > 60:
        st.info("⏰ 转账时间较长，建议在非高峰时段进行")


def _display_no_paths_found():
    """显示未找到路径的信息"""
    st.error("❌ 未找到可用的转账路径")
    
    # 显示可能的原因
    st.write("**可能原因:**")
    st.write("- 选择的平台不支持该代币")
    st.write("- 转账金额超出限制")
    st.write("- 网络暂时不可用")
    st.write("- 平台间无直接连接")


def _render_transfer_help():
    """渲染转账功能说明"""
    with st.expander("ℹ️ 功能说明", expanded=False):
        st.markdown("""
        **转账路径规划器功能包括：**
        
        🎯 **智能路径规划**
        - 自动寻找最优转账路径
        - 支持直接转账、跨链转账、多跳转账
        - 综合考虑费用、时间、风险因素
        
        💰 **费用优化**
        - 实时计算Gas费用和手续费
        - 对比不同路径的总成本
        - 提供费用优化建议
        
        ⏱️ **时间预估**
        - 准确预估转账完成时间
        - 考虑网络拥堵情况
        - 提供最快路径选择
        
        🛡️ **风险评估**
        - 评估转账成功率
        - 分析潜在风险因素
        - 提供风险等级标识
        
        📊 **可视化分析**
        - 路径对比图表
        - 效率分数雷达图
        - 实时监控面板
        
        🔧 **支持平台**
        - 主流区块链网络 (Ethereum, BSC, Polygon, Arbitrum)
        - 知名交易所 (Binance, OKX, Bybit)
        - 跨链桥协议 (Stargate, Multichain, cBridge)
        """)


def render_arbitrage_opportunities():
    """渲染期现套利机会界面"""
    st.subheader("💰 期现套利机会视图")
    
    # 控制面板
    _render_arbitrage_control_panel()
    
    # 扫描和显示套利机会
    _handle_arbitrage_scanning()


def _render_arbitrage_control_panel():
    """渲染套利控制面板"""
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        selected_symbols = st.multiselect(
            "选择交易对",
            options=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", "XRPUSDT", "DOTUSDT", "LINKUSDT"],
            default=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            help="选择要分析的交易对"
        )
    
    with col2:
        selected_exchanges = st.multiselect(
            "选择交易所",
            options=["binance", "okx", "bybit"],
            default=["binance", "okx"],
            help="选择要监控的交易所"
        )
    
    with col3:
        analysis_type = st.selectbox(
            "分析类型",
            options=["单交易所套利", "跨交易所套利", "综合分析"],
            index=0,
            help="选择套利分析类型"
        )
    
    with col4:
        if st.button("🔍 扫描机会", type="primary"):
            st.session_state.scan_arbitrage = True


def _handle_arbitrage_scanning():
    """处理套利机会扫描"""
    selected_symbols = st.session_state.get('selected_symbols', [])
    selected_exchanges = st.session_state.get('selected_exchanges', [])
    
    if not selected_symbols or not selected_exchanges:
        st.warning("请选择至少一个交易对和一个交易所")
        return
    
    # 扫描套利机会
    if st.session_state.get('scan_arbitrage', False):
        with st.spinner("正在扫描套利机会..."):
            # 这里可以添加实际的套利扫描逻辑
            st.success("套利机会扫描完成！")
            st.info("此功能正在开发中，敬请期待...")