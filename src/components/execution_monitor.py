"""
执行监控组件 - 专业套利交易系统
提供实时执行监控、P&L分析、滑点分析和风险控制功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .risk_assessment import ChartRenderer as RiskChartRenderer

# 配置常量
CURRENCIES = ["BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOGE", "MATIC", "AVAX"]
EXCHANGES = ["Binance", "OKX", "Gate.io", "Huobi", "KuCoin", "Bybit"]
ORDER_STATUSES = ["执行中", "已完成", "已取消", "失败"]

# 状态颜色映射
STATUS_COLORS = {
    "执行中": "#fff3cd",      # 黄色
    "已完成": "#d4edda",      # 绿色
    "已取消": "#f8f9fa",      # 灰色
    "失败": "#f8d7da"         # 红色
}

# 图表配置
CHART_CONFIG = {
    "height": 400,
    "color_primary": "#2E86AB",
    "color_secondary": "#A23B72",
    "color_success": "#28a745",
    "color_warning": "#ffc107",
    "color_danger": "#dc3545"
}


@dataclass
class ExecutionOrder:
    """执行订单数据类"""
    order_id: str
    currency: str
    buy_exchange: str
    sell_exchange: str
    amount: float
    status: str
    progress: int
    expected_profit: float
    realized_pnl: float
    unrealized_pnl: float
    slippage: float
    execution_time: float
    start_time: datetime
    
    def to_display_dict(self) -> Dict:
        """转换为显示格式"""
        return {
            "订单ID": self.order_id,
            "币种": self.currency,
            "买入平台": self.buy_exchange,
            "卖出平台": self.sell_exchange,
            "金额": f"${self.amount:,.2f}",
            "状态": self.status,
            "进度": f"{self.progress}%",
            "预期收益": f"${self.expected_profit:.2f}",
            "已实现P&L": f"${self.realized_pnl:.2f}",
            "未实现P&L": f"${self.unrealized_pnl:.2f}",
            "滑点": f"{self.slippage:.3f}%" if self.slippage != 0 else "-",
            "执行时间": f"{self.execution_time:.1f}分钟" if self.execution_time > 0 else "-",
            "开始时间": self.start_time.strftime("%H:%M:%S")
        }


class ExecutionDataGenerator:
    """执行数据生成器"""
    
    @staticmethod
    def generate_mock_orders(count: Optional[int] = None) -> List[ExecutionOrder]:
        """生成模拟执行订单"""
        if count is None:
            count = random.randint(5, 15)
        
        orders = []
        
        for i in range(count):
            order = ExecutionDataGenerator._create_single_order(i)
            orders.append(order)
        
        return orders
    
    @staticmethod
    def _create_single_order(index: int) -> ExecutionOrder:
        """创建单个订单"""
        currency = random.choice(CURRENCIES)
        buy_exchange = random.choice(EXCHANGES)
        sell_exchange = random.choice([ex for ex in EXCHANGES if ex != buy_exchange])
        status = random.choice(ORDER_STATUSES)
        
        # 基础数据
        amount = round(random.uniform(1000, 50000), 2)
        expected_profit = round(random.uniform(50, 500), 2)
        start_time = datetime.now() - timedelta(minutes=random.randint(5, 120))
        
        # 根据状态计算相关数据
        if status == "执行中":
            progress = random.randint(10, 90)
            realized_pnl = 0
            unrealized_pnl = round(expected_profit * (progress / 100) * random.uniform(0.8, 1.2), 2)
            slippage = 0
            execution_time = 0
        elif status == "已完成":
            progress = 100
            realized_pnl = round(expected_profit * random.uniform(0.7, 1.1), 2)
            unrealized_pnl = 0
            slippage = round(random.uniform(-0.5, 0.3), 3)
            execution_time = round(random.uniform(2, 15), 1)
        elif status == "失败":
            progress = random.randint(5, 80)
            realized_pnl = round(random.uniform(-50, -10), 2)
            unrealized_pnl = 0
            slippage = round(random.uniform(-1.0, -0.1), 3)
            execution_time = round(random.uniform(1, 8), 1)
        else:  # 已取消
            progress = random.randint(5, 50)
            realized_pnl = round(random.uniform(-20, 0), 2)
            unrealized_pnl = 0
            slippage = 0
            execution_time = 0
        
        return ExecutionOrder(
            order_id=f"ARB{1000 + index}",
            currency=currency,
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            amount=amount,
            status=status,
            progress=progress,
            expected_profit=expected_profit,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            slippage=slippage,
            execution_time=execution_time,
            start_time=start_time
        )
    
    @staticmethod
    def generate_pnl_timeseries(hours: int = 24) -> Dict[str, List]:
        """生成P&L时间序列数据"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        timestamps = []
        pnl_values = []
        
        current_time = start_time
        cumulative_pnl = 0
        
        while current_time <= end_time:
            timestamps.append(current_time)
            
            # 模拟P&L变化 - 更真实的波动
            base_change = random.uniform(-30, 60)
            volatility = random.uniform(0.5, 2.0)
            change = base_change * volatility
            
            cumulative_pnl += change
            pnl_values.append(cumulative_pnl)
            
            current_time += timedelta(minutes=30)
        
        return {
            'timestamp': timestamps,
            'cumulative_pnl': pnl_values
        }


class ExecutionMetrics:
    """执行指标计算器"""
    
    @staticmethod
    def calculate_overview_metrics(orders: List[ExecutionOrder]) -> Dict:
        """计算概览指标"""
        if not orders:
            return {
                "active_orders": 0,
                "completed_orders": 0,
                "failed_orders": 0,
                "total_realized_pnl": 0,
                "total_unrealized_pnl": 0,
                "success_rate": 0,
                "avg_execution_time": 0
            }
        
        active_orders = len([o for o in orders if o.status == "执行中"])
        completed_orders = len([o for o in orders if o.status == "已完成"])
        failed_orders = len([o for o in orders if o.status in ["失败", "已取消"]])
        
        total_realized_pnl = sum([o.realized_pnl for o in orders])
        total_unrealized_pnl = sum([o.unrealized_pnl for o in orders])
        
        completed_and_failed = completed_orders + failed_orders
        success_rate = (completed_orders / completed_and_failed * 100) if completed_and_failed > 0 else 0
        
        execution_times = [o.execution_time for o in orders if o.execution_time > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "active_orders": active_orders,
            "completed_orders": completed_orders,
            "failed_orders": failed_orders,
            "total_realized_pnl": total_realized_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time
        }


class ChartRenderer:
    """图表渲染器"""
    
    @staticmethod
    def render_pnl_chart(pnl_data: Dict[str, List]) -> go.Figure:
        """渲染P&L走势图"""
        fig = go.Figure()
        
        # 添加累计P&L线
        fig.add_trace(go.Scatter(
            x=pnl_data['timestamp'],
            y=pnl_data['cumulative_pnl'],
            mode='lines+markers',
            name='累计P&L',
            line=dict(color=CHART_CONFIG["color_primary"], width=3),
            marker=dict(size=6),
            hovertemplate='<b>时间</b>: %{x}<br><b>累计P&L</b>: $%{y:,.2f}<extra></extra>'
        ))
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="累计P&L走势",
            xaxis_title="时间",
            yaxis_title="P&L ($)",
            height=CHART_CONFIG["height"],
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def render_slippage_chart(slippage_data: List[float]) -> go.Figure:
        """渲染滑点分布图"""
        if not slippage_data:
            return None
        
        fig = px.histogram(
            x=slippage_data,
            nbins=min(10, len(slippage_data)),
            title="滑点分布",
            labels={'x': '滑点 (%)', 'y': '频次'},
            color_discrete_sequence=[CHART_CONFIG["color_secondary"]]
        )
        
        fig.update_layout(height=300)
        return fig
    
    @staticmethod
    def render_execution_time_chart(execution_times: List[float]) -> go.Figure:
        """渲染执行时间分布图"""
        if not execution_times:
            return None
        
        fig = px.box(
            y=execution_times,
            title="执行时间分布",
            labels={'y': '执行时间 (分钟)'},
            color_discrete_sequence=[CHART_CONFIG["color_primary"]]
        )
        
        fig.update_layout(height=300)
        return fig


def highlight_order_status(row) -> List[str]:
    """为订单表格行添加状态颜色"""
    try:
        status = row["状态"]
        color = STATUS_COLORS.get(status, "#ffffff")
        
        # 对于已完成订单，根据P&L调整颜色
        if status == "已完成":
            pnl_str = row["已实现P&L"].replace("$", "").replace(",", "")
            pnl_value = float(pnl_str)
            if pnl_value < 0:
                color = STATUS_COLORS["失败"]
        
        return [f'background-color: {color}'] * len(row)
    except Exception:
        return [''] * len(row)


def render_overview_metrics(metrics: Dict):
    """渲染概览指标"""
    st.subheader("📊 执行概览")
    
    # 第一行指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("执行中订单", metrics["active_orders"])
    
    with col2:
        st.metric("已完成订单", metrics["completed_orders"])
    
    with col3:
        st.metric("已实现P&L", f"${metrics['total_realized_pnl']:,.2f}")
    
    with col4:
        st.metric("未实现P&L", f"${metrics['total_unrealized_pnl']:,.2f}")
    
    # 第二行指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("失败订单", metrics["failed_orders"])
    
    with col2:
        st.metric("成功率", f"{metrics['success_rate']:.1f}%")
    
    with col3:
        st.metric("平均执行时间", f"{metrics['avg_execution_time']:.1f}分钟")
    
    with col4:
        total_orders = metrics["active_orders"] + metrics["completed_orders"] + metrics["failed_orders"]
        st.metric("总订单数", total_orders)


def render_execution_table(orders: List[ExecutionOrder]):
    """渲染执行详情表格"""
    if not orders:
        st.info("当前没有执行订单")
        return
    
    st.subheader("📋 执行详情")
    
    # 转换为显示格式
    display_data = [order.to_display_dict() for order in orders]
    df = pd.DataFrame(display_data)
    
    # 应用样式
    styled_df = df.style.apply(highlight_order_status, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # 状态说明
    st.markdown("""
    **状态说明：**
    - 🟡 执行中：订单正在执行
    - 🟢 已完成：订单成功完成
    - 🔴 失败：订单执行失败
    - ⚫ 已取消：订单被取消
    """)


def render_analysis_charts(orders: List[ExecutionOrder], pnl_data: Dict[str, List]):
    """渲染分析图表"""
    # P&L走势图
    st.markdown("---")
    st.subheader("📈 实时P&L走势")
    
    pnl_fig = ChartRenderer.render_pnl_chart(pnl_data)
    st.plotly_chart(pnl_fig, use_container_width=True)
    
    # 滑点和执行时间分析
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 滑点分析")
        completed_orders = [o for o in orders if o.status == "已完成"]
        slippage_data = [o.slippage for o in completed_orders if o.slippage != 0]
        
        if slippage_data:
            slippage_fig = ChartRenderer.render_slippage_chart(slippage_data)
            st.plotly_chart(slippage_fig, use_container_width=True)
        else:
            st.info("暂无滑点数据")
    
    with col2:
        st.subheader("⏱️ 执行时间分析")
        execution_times = [o.execution_time for o in orders if o.execution_time > 0]
        
        if execution_times:
            time_fig = ChartRenderer.render_execution_time_chart(execution_times)
            st.plotly_chart(time_fig, use_container_width=True)
        else:
            st.info("暂无执行时间数据")


@st.cache_data(ttl=30)
def get_execution_data() -> Tuple[List[ExecutionOrder], Dict[str, List]]:
    """获取执行数据（带缓存）"""
    orders = ExecutionDataGenerator.generate_mock_orders()
    pnl_data = ExecutionDataGenerator.generate_pnl_timeseries()
    return orders, pnl_data


def render_execution_monitor():
    """渲染实时执行监控界面"""
    st.subheader("⚡ 实时执行监控")
    
    try:
        # 获取数据
        orders, pnl_data = get_execution_data()
        
        # 计算指标
        metrics = ExecutionMetrics.calculate_overview_metrics(orders)
        
        # 渲染各个部分
        render_overview_metrics(metrics)
        st.markdown("---")
        render_execution_table(orders)
        render_analysis_charts(orders, pnl_data)
        
        # 刷新按钮
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 刷新数据"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            st.markdown(f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    except Exception as e:
        st.error(f"加载执行监控数据时出错: {str(e)}")
        st.info("请刷新页面重试")


def render_risk_dashboard():
    """渲染风险控制仪表盘"""
    try:
        from .risk_assessment import render_risk_assessment
        render_risk_assessment()
    except Exception as e:
        st.error(f"加载风险评估组件时出错: {str(e)}")
        st.info("请检查风险评估组件配置")