"""
风险评估组件 - 专业套利交易系统
提供VaR分析、压力测试、投资组合风险评估和风险管理建议
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 风险配置常量
class RiskLevel(Enum):
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    CRITICAL = "极高风险"

# 风险评估配置
RISK_CONFIG = {
    "var_confidence_levels": [0.95, 0.99],
    "simulation_days": 30,
    "simulation_samples": 1000,
    "risk_categories": ['流动性风险', '市场风险', '技术风险', '对手方风险', '操作风险', '监管风险'],
    "stress_scenarios": {
        '正常市场': {'impact': 0.02, 'probability': 0.70, 'color': 'green'},
        '高波动': {'impact': -0.15, 'probability': 0.15, 'color': 'yellow'},
        '流动性危机': {'impact': -0.25, 'probability': 0.08, 'color': 'orange'},
        '黑天鹅事件': {'impact': -0.40, 'probability': 0.02, 'color': 'red'},
        '监管冲击': {'impact': -0.20, 'probability': 0.05, 'color': 'purple'}
    },
    "default_assets": ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'],
    "chart_colors": {
        "primary": "#2E86AB",
        "secondary": "#A23B72", 
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8"
    }
}

# 风险阈值配置
RISK_THRESHOLDS = {
    "var_95": {"low": -0.05, "medium": -0.10, "high": -0.20},
    "volatility": {"low": 0.10, "medium": 0.20, "high": 0.35},
    "sharpe_ratio": {"excellent": 2.0, "good": 1.0, "poor": 0.5},
    "max_drawdown": {"low": -0.05, "medium": -0.15, "high": -0.30},
    "win_rate": {"excellent": 0.70, "good": 0.60, "poor": 0.50}
}


@dataclass
class RiskMetrics:
    """风险指标数据类"""
    var_95: float
    var_99: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    avg_return: float
    win_rate: float
    
    def get_risk_level(self) -> RiskLevel:
        """根据指标计算整体风险等级"""
        risk_score = 0
        
        # VaR评分
        if self.var_95 < RISK_THRESHOLDS["var_95"]["high"]:
            risk_score += 3
        elif self.var_95 < RISK_THRESHOLDS["var_95"]["medium"]:
            risk_score += 2
        elif self.var_95 < RISK_THRESHOLDS["var_95"]["low"]:
            risk_score += 1
        
        # 波动率评分
        if self.volatility > RISK_THRESHOLDS["volatility"]["high"]:
            risk_score += 3
        elif self.volatility > RISK_THRESHOLDS["volatility"]["medium"]:
            risk_score += 2
        elif self.volatility > RISK_THRESHOLDS["volatility"]["low"]:
            risk_score += 1
        
        # 最大回撤评分
        if self.max_drawdown < RISK_THRESHOLDS["max_drawdown"]["high"]:
            risk_score += 3
        elif self.max_drawdown < RISK_THRESHOLDS["max_drawdown"]["medium"]:
            risk_score += 2
        elif self.max_drawdown < RISK_THRESHOLDS["max_drawdown"]["low"]:
            risk_score += 1
        
        # 根据总分确定风险等级
        if risk_score >= 7:
            return RiskLevel.CRITICAL
        elif risk_score >= 5:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_sharpe_rating(self) -> str:
        """获取夏普比率评级"""
        if self.sharpe_ratio >= RISK_THRESHOLDS["sharpe_ratio"]["excellent"]:
            return "优秀"
        elif self.sharpe_ratio >= RISK_THRESHOLDS["sharpe_ratio"]["good"]:
            return "良好"
        elif self.sharpe_ratio >= RISK_THRESHOLDS["sharpe_ratio"]["poor"]:
            return "一般"
        else:
            return "较差"
    
    def get_win_rate_rating(self) -> str:
        """获取胜率评级"""
        if self.win_rate >= RISK_THRESHOLDS["win_rate"]["excellent"]:
            return "优秀"
        elif self.win_rate >= RISK_THRESHOLDS["win_rate"]["good"]:
            return "良好"
        else:
            return "需改进"


class RiskCalculator:
    """风险计算器"""
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """计算风险价值(VaR)"""
        try:
            if len(returns) == 0:
                return 0.0
            return float(np.percentile(returns, (1 - confidence_level) * 100))
        except Exception:
            return 0.0
    
    @staticmethod
    def generate_risk_metrics() -> RiskMetrics:
        """生成风险评估指标"""
        try:
            # 模拟历史收益率数据
            days = RISK_CONFIG["simulation_days"]
            returns = np.random.normal(0.02, 0.15, days)  # 平均2%收益，15%波动率
            
            # 计算各种风险指标
            var_95 = RiskCalculator.calculate_var(returns, 0.95)
            var_99 = RiskCalculator.calculate_var(returns, 0.99)
            volatility = float(np.std(returns))
            avg_return = float(np.mean(returns))
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0.0
            
            # 计算最大回撤
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = cumulative_returns - running_max
            max_drawdown = float(np.min(drawdowns))
            
            win_rate = float(len(returns[returns > 0]) / len(returns))
            
            return RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                avg_return=avg_return,
                win_rate=win_rate
            )
        except Exception as e:
            st.error(f"生成风险指标时出错: {str(e)}")
            # 返回默认值
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0)
    
    @staticmethod
    def generate_strategy_risk_scores() -> Dict[str, List[int]]:
        """生成策略风险评分"""
        return {
            '跨交易所套利': [8, 6, 7, 5, 6, 4],
            '三角套利': [9, 7, 8, 3, 7, 3],
            '期现套利': [7, 8, 6, 6, 5, 7],
            '统计套利': [6, 9, 5, 4, 8, 5]
        }
    
    @staticmethod
    def generate_correlation_matrix(assets: List[str]) -> np.ndarray:
        """生成资产相关性矩阵"""
        try:
            n = len(assets)
            # 生成随机相关性矩阵
            correlation_matrix = np.random.rand(n, n)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1)
            
            # 确保矩阵是正定的
            eigenvals = np.linalg.eigvals(correlation_matrix)
            if np.min(eigenvals) <= 0:
                correlation_matrix += np.eye(n) * (0.01 - np.min(eigenvals))
            
            return correlation_matrix
        except Exception:
            # 返回单位矩阵作为默认值
            return np.eye(len(assets))


class ChartRenderer:
    """图表渲染器"""
    
    @staticmethod
    def render_risk_radar_chart() -> Optional[go.Figure]:
        """渲染风险评分雷达图"""
        try:
            categories = RISK_CONFIG["risk_categories"]
            strategies = RiskCalculator.generate_strategy_risk_scores()
            
            fig = go.Figure()
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            for i, (strategy, scores) in enumerate(strategies.items()):
                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=categories,
                    fill='toself',
                    name=strategy,
                    line_color=colors[i % len(colors)],
                    fillcolor=colors[i % len(colors)],
                    opacity=0.3
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10]
                    )),
                showlegend=True,
                title="套利策略风险评分雷达图",
                height=500
            )
            
            return fig
        except Exception as e:
            st.error(f"渲染雷达图时出错: {str(e)}")
            return None
    
    @staticmethod
    def render_var_analysis() -> Optional[go.Figure]:
        """渲染VaR分析图表"""
        try:
            # 生成模拟收益率分布
            returns = np.random.normal(0.02, 0.15, RISK_CONFIG["simulation_samples"])
            
            fig = go.Figure()
            
            # 添加收益率分布直方图
            fig.add_trace(go.Histogram(
                x=returns,
                nbinsx=50,
                name='收益率分布',
                opacity=0.7,
                marker_color=RISK_CONFIG["chart_colors"]["info"]
            ))
            
            # 添加VaR线
            var_95 = RiskCalculator.calculate_var(returns, 0.95)
            var_99 = RiskCalculator.calculate_var(returns, 0.99)
            
            fig.add_vline(
                x=var_95, 
                line_dash="dash", 
                line_color=RISK_CONFIG["chart_colors"]["warning"], 
                annotation_text=f"VaR 95%: {var_95:.3f}"
            )
            fig.add_vline(
                x=var_99, 
                line_dash="dash", 
                line_color=RISK_CONFIG["chart_colors"]["danger"], 
                annotation_text=f"VaR 99%: {var_99:.3f}"
            )
            
            fig.update_layout(
                title="收益率分布与风险价值(VaR)分析",
                xaxis_title="收益率",
                yaxis_title="频次",
                height=400
            )
            
            return fig
        except Exception as e:
            st.error(f"渲染VaR分析图时出错: {str(e)}")
            return None
    
    @staticmethod
    def render_correlation_heatmap(assets: List[str]) -> Tuple[Optional[go.Figure], np.ndarray]:
        """渲染相关性热力图"""
        try:
            correlation_matrix = RiskCalculator.generate_correlation_matrix(assets)
            
            fig = px.imshow(
                correlation_matrix,
                x=assets,
                y=assets,
                color_continuous_scale='RdYlBu_r',
                title="资产相关性矩阵",
                aspect="auto"
            )
            
            fig.update_layout(height=400)
            
            # 生成权重
            weights = np.random.dirichlet(np.ones(len(assets)))
            
            return fig, weights
        except Exception as e:
            st.error(f"渲染相关性热力图时出错: {str(e)}")
            return None, np.array([])
    
    @staticmethod
    def render_stress_test() -> Optional[go.Figure]:
        """渲染压力测试结果"""
        try:
            scenarios = list(RISK_CONFIG["stress_scenarios"].keys())
            impacts = [data['impact'] for data in RISK_CONFIG["stress_scenarios"].values()]
            probabilities = [data['probability'] for data in RISK_CONFIG["stress_scenarios"].values()]
            colors = [data['color'] for data in RISK_CONFIG["stress_scenarios"].values()]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=scenarios,
                y=impacts,
                marker_color=colors,
                text=[f'{p:.1%}' for p in probabilities],
                textposition='auto',
                name='预期影响',
                hovertemplate='<b>场景</b>: %{x}<br><b>影响</b>: %{y:.1%}<br><b>概率</b>: %{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title="压力测试场景分析",
                xaxis_title="市场场景",
                yaxis_title="预期收益影响",
                yaxis_tickformat='.1%',
                height=400
            )
            
            return fig
        except Exception as e:
            st.error(f"渲染压力测试图时出错: {str(e)}")
            return None


def render_risk_metrics_overview(risk_metrics: RiskMetrics):
    """渲染风险指标概览"""
    st.subheader("📊 风险指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "VaR (95%)",
            f"{risk_metrics.var_95:.3f}",
            delta=f"{risk_metrics.var_95*100:.1f}%"
        )
    
    with col2:
        st.metric(
            "波动率",
            f"{risk_metrics.volatility:.3f}",
            delta=f"{risk_metrics.volatility*100:.1f}%"
        )
    
    with col3:
        st.metric(
            "夏普比率",
            f"{risk_metrics.sharpe_ratio:.2f}",
            delta=risk_metrics.get_sharpe_rating()
        )
    
    with col4:
        st.metric(
            "胜率",
            f"{risk_metrics.win_rate:.1%}",
            delta=risk_metrics.get_win_rate_rating()
        )


def render_risk_charts():
    """渲染风险分析图表"""
    st.subheader("📈 风险分析图表")
    
    col1, col2 = st.columns(2)
    
    with col1:
        radar_fig = ChartRenderer.render_risk_radar_chart()
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True)
    
    with col2:
        var_fig = ChartRenderer.render_var_analysis()
        if var_fig:
            st.plotly_chart(var_fig, use_container_width=True)


def render_portfolio_analysis():
    """渲染投资组合分析"""
    st.subheader("📊 投资组合风险分析")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        assets = RISK_CONFIG["default_assets"]
        corr_fig, weights = ChartRenderer.render_correlation_heatmap(assets)
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True)
    
    with col2:
        if len(weights) > 0:
            st.write("**当前权重分配:**")
            for asset, weight in zip(assets, weights):
                st.write(f"• {asset}: {weight:.1%}")
        else:
            st.info("权重数据加载中...")


def render_stress_test_section():
    """渲染压力测试部分"""
    st.subheader("⚠️ 压力测试分析")
    
    stress_fig = ChartRenderer.render_stress_test()
    if stress_fig:
        st.plotly_chart(stress_fig, use_container_width=True)


def render_risk_recommendations(risk_metrics: RiskMetrics):
    """渲染风险管理建议"""
    st.subheader("💡 风险管理建议")
    
    risk_level = risk_metrics.get_risk_level()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 根据风险等级显示不同的信息
        if risk_level == RiskLevel.LOW:
            st.success(f"""
            **当前风险状态: {risk_level.value}**
            
            • VaR指标表现良好
            • 投资组合风险可控
            • 可适当增加仓位
            """)
        elif risk_level == RiskLevel.MEDIUM:
            st.info(f"""
            **当前风险状态: {risk_level.value}**
            
            • VaR指标显示潜在损失可控
            • 投资组合分散度适中
            • 建议关注流动性风险
            """)
        elif risk_level == RiskLevel.HIGH:
            st.warning(f"""
            **当前风险状态: {risk_level.value}**
            
            • 风险指标偏高，需要关注
            • 建议降低仓位规模
            • 加强风险监控
            """)
        else:  # CRITICAL
            st.error(f"""
            **当前风险状态: {risk_level.value}**
            
            • 风险指标严重超标
            • 立即降低仓位
            • 暂停新增交易
            """)
    
    with col2:
        # 风险控制措施
        if risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            st.info("""
            **风险控制措施:**
            
            • 设置止损点位: -5%
            • 单笔交易限额: 10%
            • 实时监控市场异动
            """)
        else:
            st.warning("""
            **紧急风险控制措施:**
            
            • 设置止损点位: -3%
            • 单笔交易限额: 5%
            • 24小时风险监控
            • 准备应急预案
            """)


@st.cache_data(ttl=60)
def get_risk_data() -> RiskMetrics:
    """获取风险数据（带缓存）"""
    return RiskCalculator.generate_risk_metrics()


def render_risk_assessment():
    """渲染完整的风险评估界面"""
    st.header("🛡️ 智能风险评估系统")
    
    try:
        # 获取风险数据
        risk_metrics = get_risk_data()
        
        # 渲染各个部分
        render_risk_metrics_overview(risk_metrics)
        st.markdown("---")
        render_risk_charts()
        st.markdown("---")
        render_portfolio_analysis()
        st.markdown("---")
        render_stress_test_section()
        st.markdown("---")
        render_risk_recommendations(risk_metrics)
        
        # 刷新按钮
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 刷新风险数据"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            st.markdown(f"*最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    except Exception as e:
        st.error(f"加载风险评估系统时出错: {str(e)}")
        st.info("请刷新页面重试或联系技术支持")