"""
系统设置组件模块
包含系统设置页面的所有渲染函数
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from typing import Dict, List, Any

from ..core.alerts import alert_system, AlertRule, AlertType, AlertSeverity, NotificationChannel
from ..core.account_manager import account_manager, AccountInfo, AccountType, AccountStatus


def render_system_settings(config: Dict):
    """渲染系统设置页面"""
    st.title("⚙️ 系统设置")
    st.markdown("---")
    
    # 设置选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚙️ 基础设置", 
        "🔑 API配置", 
        "🎨 显示设置", 
        "🚨 预警系统", 
        "👥 多账户管理"
    ])
    
    with tab1:
        _render_basic_settings()
    
    with tab2:
        _render_api_configuration()
    
    with tab3:
        _render_display_settings()
    
    with tab4:
        _render_alert_system()
    
    with tab5:
        _render_account_management()


def _render_basic_settings():
    """渲染基础设置标签页"""
    st.subheader("🔧 基础设置")
    
    # 风险设置
    st.write("### ⚠️ 风险管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_position_size = st.slider(
            "最大仓位比例 (%)",
            min_value=1,
            max_value=100,
            value=st.session_state.get('max_position_size', 20),
            key="settings_max_position"
        )
    
    with col2:
        max_daily_loss = st.slider(
            "最大日损失 (%)",
            min_value=1,
            max_value=20,
            value=st.session_state.get('max_daily_loss', 5),
            key="settings_max_loss"
        )
    
    # 保存设置
    if st.button("💾 保存基础设置"):
        st.session_state.max_position_size = max_position_size
        st.session_state.max_daily_loss = max_daily_loss
        st.success("✅ 基础设置已保存！")


def _render_api_configuration():
    """渲染API配置标签页"""
    st.subheader("🔐 API配置")
    
    # API密钥管理
    st.write("### 🔑 API密钥管理")
    
    exchanges = ["Binance", "OKX", "Bybit", "Huobi", "KuCoin"]
    
    for exchange in exchanges:
        with st.expander(f"{exchange} API配置"):
            col1, col2 = st.columns(2)
            
            with col1:
                api_key = st.text_input(
                    "API密钥",
                    type="password",
                    key=f"{exchange.lower()}_api_key"
                )
            
            with col2:
                secret_key = st.text_input(
                    "密钥",
                    type="password",
                    key=f"{exchange.lower()}_secret_key"
                )
            
            # 测试连接
            if st.button(f"🔍 测试 {exchange} 连接", key=f"test_{exchange.lower()}"):
                if api_key and secret_key:
                    with st.spinner(f"正在测试 {exchange} 连接..."):
                        time.sleep(1)
                        st.success(f"✅ {exchange} 连接成功！")
                else:
                    st.error("❌ 请填写完整的API密钥信息")


def _render_display_settings():
    """渲染显示设置标签页"""
    st.subheader("📊 显示设置")
    
    # 界面设置
    st.write("### 🎨 界面设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "主题",
            ["自动", "浅色", "深色"],
            index=0
        )
    
    with col2:
        language = st.selectbox(
            "语言",
            ["中文", "English"],
            index=0
        )
    
    # 数据刷新设置
    st.write("### 🔄 数据刷新")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_refresh = st.checkbox(
            "启用自动刷新",
            value=st.session_state.get('auto_refresh_enabled', False)
        )
    
    with col2:
        refresh_interval = st.selectbox(
            "刷新间隔 (秒)",
            [5, 10, 15, 30, 60],
            index=1
        )
    
    if st.button("💾 保存显示设置"):
        st.session_state.auto_refresh_enabled = auto_refresh
        st.session_state.auto_refresh_interval = refresh_interval
        st.success("✅ 显示设置已保存！")


def _render_alert_system():
    """渲染预警系统标签页"""
    st.subheader("🚨 预警系统")
    
    # 预警规则管理
    st.write("### 📋 预警规则管理")
    
    # 显示当前规则
    _display_alert_rules()
    
    # 添加新规则表单
    _render_add_rule_form()
    
    st.markdown("---")
    
    # 活跃预警
    _display_active_alerts()
    
    # 通知设置
    _render_notification_settings()


def _display_alert_rules():
    """显示当前预警规则"""
    rules_col1, rules_col2 = st.columns([2, 1])
    
    with rules_col1:
        st.write("**当前预警规则**")
        
        rules_data = []
        for rule in alert_system.rules.values():
            rules_data.append({
                "规则名称": rule.name,
                "类型": rule.alert_type.value,
                "严重程度": rule.severity.value,
                "状态": "启用" if rule.enabled else "禁用",
                "冷却时间": f"{rule.cooldown_minutes}分钟"
            })
        
        if rules_data:
            rules_df = pd.DataFrame(rules_data)
            st.dataframe(rules_df, use_container_width=True)
        else:
            st.info("暂无预警规则")
    
    with rules_col2:
        st.write("**快速操作**")
        
        if st.button("➕ 添加规则"):
            st.session_state.show_add_rule = True
        
        if st.button("📊 预警统计"):
            stats = alert_system.get_alert_statistics()
            st.json(stats)


def _render_add_rule_form():
    """渲染添加新规则表单"""
    if st.session_state.get('show_add_rule', False):
        st.write("### ➕ 添加新预警规则")
        
        with st.form("add_alert_rule"):
            rule_col1, rule_col2 = st.columns(2)
            
            with rule_col1:
                rule_name = st.text_input("规则名称", placeholder="输入规则名称")
                rule_type = st.selectbox(
                    "预警类型",
                    [t.value for t in AlertType],
                    format_func=lambda x: {
                        "spread_alert": "价差预警",
                        "arbitrage_opportunity": "套利机会",
                        "market_anomaly": "市场异常",
                        "volume_alert": "交易量预警",
                        "price_alert": "价格预警",
                        "system_error": "系统错误"
                    }.get(x, x)
                )
                rule_severity = st.selectbox(
                    "严重程度",
                    [s.value for s in AlertSeverity],
                    format_func=lambda x: {
                        "low": "低",
                        "medium": "中",
                        "high": "高", 
                        "critical": "严重"
                    }.get(x, x)
                )
            
            with rule_col2:
                cooldown_minutes = st.number_input("冷却时间(分钟)", min_value=1, max_value=1440, value=5)
                
                notification_channels = st.multiselect(
                    "通知渠道",
                    [c.value for c in NotificationChannel],
                    format_func=lambda x: {
                        "email": "邮件",
                        "webhook": "Webhook",
                        "desktop": "桌面通知",
                        "mobile": "手机推送"
                    }.get(x, x)
                )
            
            # 条件设置
            conditions = _render_rule_conditions(rule_type)
            
            submitted = st.form_submit_button("✅ 创建规则")
            
            if submitted and rule_name:
                _create_alert_rule(rule_name, rule_type, rule_severity, cooldown_minutes, notification_channels, conditions)


def _render_rule_conditions(rule_type: str) -> Dict:
    """渲染规则条件设置"""
    st.write("**触发条件**")
    
    if rule_type == "spread_alert":
        min_spread = st.number_input("最小价差百分比", min_value=0.1, max_value=10.0, value=0.5, step=0.1)
        min_volume = st.number_input("最小交易量(USD)", min_value=1000, max_value=1000000, value=10000, step=1000)
        return {"min_spread_percentage": min_spread, "min_volume_usd": min_volume}
    
    elif rule_type == "arbitrage_opportunity":
        min_profit = st.number_input("最小利润百分比", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
        max_exec_time = st.number_input("最大执行时间(秒)", min_value=1, max_value=300, value=30)
        min_liquidity = st.number_input("最小流动性(USD)", min_value=10000, max_value=1000000, value=50000, step=10000)
        return {
            "min_profit_percentage": min_profit,
            "max_execution_time_seconds": max_exec_time,
            "min_liquidity_usd": min_liquidity
        }
    
    elif rule_type == "market_anomaly":
        price_threshold = st.number_input("价格变动阈值(%)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)
        volume_multiplier = st.number_input("交易量激增倍数", min_value=1.5, max_value=10.0, value=3.0, step=0.5)
        return {
            "price_change_threshold": price_threshold,
            "volume_spike_multiplier": volume_multiplier
        }
    
    return {}


def _create_alert_rule(rule_name: str, rule_type: str, rule_severity: str, cooldown_minutes: int, 
                      notification_channels: List[str], conditions: Dict):
    """创建预警规则"""
    new_rule = AlertRule(
        id=f"rule_{datetime.now().timestamp()}",
        name=rule_name,
        alert_type=AlertType(rule_type),
        conditions=conditions,
        severity=AlertSeverity(rule_severity),
        cooldown_minutes=cooldown_minutes,
        channels=[NotificationChannel(c) for c in notification_channels]
    )
    
    if alert_system.add_rule(new_rule):
        st.success(f"✅ 预警规则 '{rule_name}' 创建成功！")
        st.session_state.show_add_rule = False
        st.rerun()
    else:
        st.error("❌ 创建预警规则失败")


def _display_active_alerts():
    """显示活跃预警"""
    st.write("### 🔔 活跃预警")
    
    active_alerts = alert_system.get_active_alerts()
    
    if active_alerts:
        for alert in active_alerts[-10:]:  # 显示最近10条
            severity_color = {
                "low": "blue",
                "medium": "orange", 
                "high": "red",
                "critical": "purple"
            }.get(alert.severity.value, "gray")
            
            with st.expander(f"🚨 {alert.title} - {alert.timestamp.strftime('%H:%M:%S')}"):
                st.markdown(f"**严重程度**: <span style='color: {severity_color}'>{alert.severity.value.upper()}</span>", 
                           unsafe_allow_html=True)
                st.write(f"**消息**: {alert.message}")
                st.write(f"**类型**: {alert.alert_type.value}")
                st.write(f"**时间**: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                
                alert_col1, alert_col2 = st.columns(2)
                
                with alert_col1:
                    if not alert.acknowledged and st.button(f"✅ 确认", key=f"ack_{alert.id}"):
                        alert_system.acknowledge_alert(alert.id)
                        st.success("预警已确认")
                        st.rerun()
                
                with alert_col2:
                    if not alert.resolved and st.button(f"🔧 解决", key=f"resolve_{alert.id}"):
                        alert_system.resolve_alert(alert.id)
                        st.success("预警已解决")
                        st.rerun()
    else:
        st.info("🎉 当前没有活跃预警")


def _render_notification_settings():
    """渲染通知设置"""
    st.write("### 📧 通知设置")
    
    notification_col1, notification_col2 = st.columns(2)
    
    with notification_col1:
        st.write("**邮件配置**")
        email_server = st.text_input("SMTP服务器", value="smtp.gmail.com")
        email_port = st.number_input("SMTP端口", value=587)
        email_username = st.text_input("邮箱用户名", placeholder="your-email@gmail.com")
        email_password = st.text_input("邮箱密码", type="password", placeholder="应用专用密码")
    
    with notification_col2:
        st.write("**Webhook配置**")
        webhook_url = st.text_input("Webhook地址", placeholder="https://hooks.slack.com/...")
        webhook_headers = st.text_area("请求头(JSON格式)", placeholder='{"Content-Type": "application/json"}')
    
    if st.button("💾 保存通知设置"):
        _save_notification_settings(email_server, email_port, email_username, email_password, webhook_url, webhook_headers)


def _save_notification_settings(email_server: str, email_port: int, email_username: str, 
                               email_password: str, webhook_url: str, webhook_headers: str):
    """保存通知设置"""
    # 更新通知配置
    if email_username and email_password:
        alert_system.config.email_username = email_username
        alert_system.config.email_password = email_password
        alert_system.config.email_smtp_server = email_server
        alert_system.config.email_smtp_port = email_port
    
    if webhook_url:
        alert_system.config.webhook_url = webhook_url
        try:
            if webhook_headers:
                alert_system.config.webhook_headers = json.loads(webhook_headers)
        except:
            st.warning("Webhook请求头格式不正确，使用默认设置")
    
    st.success("✅ 通知设置已保存！")


def _render_account_management():
    """渲染多账户管理标签页"""
    st.write("## 👥 多账户管理系统")
    
    # 投资组合概览
    _display_portfolio_summary()
    
    st.markdown("---")
    
    # 账户管理
    account_tab1, account_tab2, account_tab3 = st.tabs(["📋 账户列表", "➕ 添加账户", "⚖️ 资金分配"])
    
    with account_tab1:
        _render_account_list()
    
    with account_tab2:
        _render_add_account_form()
    
    with account_tab3:
        _render_fund_allocation()


def _display_portfolio_summary():
    """显示投资组合概览"""
    st.write("### 📊 投资组合概览")
    
    portfolio_summary = account_manager.get_portfolio_summary()
    
    if portfolio_summary:
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            st.metric(
                "总账户数",
                portfolio_summary.get("total_accounts", 0),
                delta=f"活跃: {portfolio_summary.get('active_accounts', 0)}"
            )
        
        with summary_col2:
            total_value = portfolio_summary.get("total_value_usd", 0)
            st.metric(
                "总资产价值 (USD)",
                f"${total_value:,.2f}",
                delta=f"{portfolio_summary.get('daily_pnl_percentage', 0):.2f}%"
            )
        
        with summary_col3:
            daily_pnl = portfolio_summary.get("daily_pnl_usd", 0)
            st.metric(
                "今日盈亏 (USD)",
                f"${daily_pnl:,.2f}",
                delta=f"{portfolio_summary.get('total_trades', 0)} 笔交易"
            )
        
        with summary_col4:
            allocation_rules = portfolio_summary.get("allocation_rules", 0)
            st.metric(
                "分配规则",
                allocation_rules,
                delta="个活跃规则"
            )


def _render_account_list():
    """渲染账户列表"""
    st.write("### 📋 账户列表")
    
    if account_manager.accounts:
        for account_id, account in account_manager.accounts.items():
            with st.expander(f"🏦 {account.exchange} - {account_id}"):
                _display_account_details(account_id, account)
                _render_account_actions(account_id, account)
    else:
        st.info("📝 还没有添加任何账户，请在'添加账户'标签页中添加。")


def _display_account_details(account_id: str, account: AccountInfo):
    """显示账户详情"""
    account_col1, account_col2 = st.columns(2)
    
    with account_col1:
        st.write(f"**交易所**: {account.exchange}")
        st.write(f"**账户类型**: {account.account_type.value}")
        st.write(f"**状态**: {account.status.value}")
        st.write(f"**创建时间**: {account.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    with account_col2:
        # 获取账户余额
        balances = account_manager.get_account_balances(account_id)
        if balances:
            st.write("**余额信息**:")
            for currency, balance in balances.items():
                st.write(f"- {currency}: {balance.total:.4f} (可用: {balance.available:.4f})")
        
        # 获取账户指标
        metrics = account_manager.get_account_metrics(account_id)
        if metrics:
            st.write("**表现指标**:")
            st.write(f"- 总价值: ${metrics.total_value_usd:,.2f}")
            st.write(f"- 日盈亏: ${metrics.daily_pnl:,.2f} ({metrics.daily_pnl_percentage:.2f}%)")
            st.write(f"- 夏普比率: {metrics.sharpe_ratio:.2f}")
            st.write(f"- 胜率: {metrics.win_rate:.1%}")


def _render_account_actions(account_id: str, account: AccountInfo):
    """渲染账户操作按钮"""
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if account.status == AccountStatus.ACTIVE:
            if st.button(f"⏸️ 暂停", key=f"pause_{account_id}"):
                account_manager.update_account_status(account_id, AccountStatus.INACTIVE)
                st.success("账户已暂停")
                st.rerun()
        else:
            if st.button(f"▶️ 激活", key=f"activate_{account_id}"):
                account_manager.update_account_status(account_id, AccountStatus.ACTIVE)
                st.success("账户已激活")
                st.rerun()
    
    with action_col2:
        if st.button(f"🔄 刷新余额", key=f"refresh_{account_id}"):
            account_manager.get_account_balances(account_id)
            st.success("余额已刷新")
            st.rerun()
    
    with action_col3:
        if st.button(f"🗑️ 删除账户", key=f"delete_{account_id}"):
            if account_manager.remove_account(account_id):
                st.success("账户已删除")
                st.rerun()
            else:
                st.error("删除账户失败")


def _render_add_account_form():
    """渲染添加账户表单"""
    st.write("### ➕ 添加新账户")
    
    with st.form("add_account_form"):
        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            account_id = st.text_input("账户ID", placeholder="my_binance_account")
            exchange = st.selectbox("交易所", ["binance", "okx", "bybit", "huobi", "kucoin"])
            account_type = st.selectbox("账户类型", [t.value for t in AccountType])
            api_key = st.text_input("API密钥", type="password")
        
        with form_col2:
            api_secret = st.text_input("API密钥", type="password")
            passphrase = st.text_input("密码短语 (可选)", type="password")
            sandbox = st.checkbox("沙盒模式")
            test_connection = st.checkbox("测试连接", value=True)
        
        submitted = st.form_submit_button("✅ 添加账户")
        
        if submitted and account_id and exchange and api_key and api_secret:
            _add_new_account(account_id, exchange, account_type, api_key, api_secret, passphrase, sandbox)


def _add_new_account(account_id: str, exchange: str, account_type: str, api_key: str, 
                    api_secret: str, passphrase: str, sandbox: bool):
    """添加新账户"""
    new_account = AccountInfo(
        account_id=account_id,
        exchange=exchange,
        account_type=AccountType(account_type),
        status=AccountStatus.ACTIVE,
        balances={},
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase if passphrase else None,
        sandbox=sandbox
    )
    
    if account_manager.add_account(new_account):
        st.success(f"✅ 账户 '{account_id}' 添加成功！")
        st.rerun()
    else:
        st.error("❌ 添加账户失败，请检查API配置")


def _render_fund_allocation():
    """渲染资金分配管理"""
    st.write("### ⚖️ 资金分配管理")
    
    # 分配规则管理
    st.write("#### 📋 分配规则")
    
    if account_manager.allocation_rules:
        for rule_id, rule in account_manager.allocation_rules.items():
            with st.expander(f"📏 {rule.name} ({'✅ 启用' if rule.enabled else '❌ 禁用'})"):
                _display_allocation_rule_details(rule_id, rule)
                _render_allocation_rule_actions(rule_id, rule)
    else:
        st.info("📝 还没有添加任何分配规则。")


def _display_allocation_rule_details(rule_id: str, rule):
    """显示分配规则详情"""
    rule_col1, rule_col2 = st.columns(2)
    
    with rule_col1:
        st.write(f"**策略**: {rule.strategy.value}")
        st.write(f"**最小分配**: ${rule.min_allocation}")
        st.write(f"**最大分配**: ${rule.max_allocation}")
        st.write(f"**重平衡阈值**: {rule.rebalance_threshold:.1%}")
    
    with rule_col2:
        st.write(f"**目标账户**: {len(rule.target_accounts) if rule.target_accounts else '所有账户'}")
        if rule.weights:
            st.write("**权重配置**:")
            for acc_id, weight in rule.weights.items():
                st.write(f"- {acc_id}: {weight:.2f}")


def _render_allocation_rule_actions(rule_id: str, rule):
    """渲染分配规则操作按钮"""
    rule_action_col1, rule_action_col2, rule_action_col3 = st.columns(3)
    
    with rule_action_col1:
        if rule.enabled:
            if st.button(f"⏸️ 禁用", key=f"disable_rule_{rule_id}"):
                rule.enabled = False
                st.success("规则已禁用")
                st.rerun()
        else:
            if st.button(f"▶️ 启用", key=f"enable_rule_{rule_id}"):
                rule.enabled = True
                st.success("规则已启用")
                st.rerun()
    
    with rule_action_col2:
        if st.button(f"🔄 执行重平衡", key=f"rebalance_{rule_id}"):
            # 执行重平衡逻辑
            st.success("重平衡已执行")
            st.rerun()
    
    with rule_action_col3:
        if st.button(f"🗑️ 删除规则", key=f"delete_rule_{rule_id}"):
            del account_manager.allocation_rules[rule_id]
            st.success("规则已删除")
            st.rerun()