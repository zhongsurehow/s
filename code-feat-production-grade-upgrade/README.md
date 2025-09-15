# 生产级数字货币交易所对比分析工具

这是一个高性能、可扩展、功能丰富的生产级数字货币分析工具。它集成了多个数据源（中心化交易所、去中心化交易所、跨链桥），提供全面的交易所对比功能，包括实时行情、市场深度、套利机会发现、费用分析和定性评估。

## 支持的交易所
本工具目前支持以下主流中心化交易所 (CEX) 的数据集成和对比：
- **Mexc**
- **Gate**
- **Kucoin**
- **Bitget**
- **Bybit**
- **HTX**
- **Binance**
- **OKX**

## 核心功能

- **多维度交易所对比**:
  - **实时行情**: 通过 `ccxt.pro` 的 WebSocket 实时获取多个交易所的行情和订单簿数据。
  - **费用分析**: 动态查询并对比不同交易所、不同资产的 **充值 (Deposit)** 和 **提现 (Withdrawal)** 网络及手续费。
  - **市场深度**: 动态、交互式地展示所选交易对的市场深度图。
  - **跨平台套利**: 内置套利引擎，实时分析价差，并精确计算扣除手续费后的净利润。
  - **定性数据对比**: 提供一个全面的、手动维护的交易所信息库 (`qualitative_data.yml`)，包含以下对比维度：
    - 安全措施 (`security_measures`)
    - 客服响应 (`customer_service`)
    - 平台稳定性 (`platform_stability`)
    - 资金保险 (`fund_insurance`)
    - 地域限制 (`regional_restrictions`)
    - 提现限制 (`withdrawal_limits`)
    - **提现速度 (`withdrawal_speed`)**
    - **支持的跨链桥 (`supported_cross_chain_bridges`)**
    - **API 支持详情 (`api_support_details`)**
    - **手续费优惠 (`fee_discounts`)**
    - **保证金/杠杆详情 (`margin_leverage_details`)**
    - **维护时间 (`maintenance_schedule`)**
    - **用户评级 (`user_rating_summary`)**
    - **税务合规性 (`tax_compliance_info`)**
- **数据持久化与历史分析**:
  - 使用 `asyncpg` 与 `PostgreSQL/TimescaleDB` 高效集成，存储实时行情数据。
  - 支持对历史数据的查询和可视化分析。
- **现代化Web界面**:
  - 基于 `Streamlit` 构建，通过清晰的标签页展示不同功能模块。
- **容器化部署**:
  - 提供 `Dockerfile` 和 `docker-compose.yml`，一键启动整个应用。

## 技术架构与原理

本项目采用模块化的架构，将不同的业务关注点分离到独立的模块中，易于维护和扩展。

### 文件结构

```
.
├── app.py                  # Streamlit 应用主入口
├── config.py               # 配置加载模块
├── db.py                   # 数据库管理器
├── engine.py               # 套利引擎
├── fees.yml                # 套利引擎的手续费配置
├── qualitative_data.yml    # 交易所定性信息数据库
├── providers/              # 数据提供者模块
│   ├── base.py             # Provider 抽象基类
│   ├── cex.py              # CEX 数据提供者 (ccxt.pro)
│   ├── ...
├── ui/                     # UI 组件模块
│   ├── ...
├── tests/                  # 测试套件
│   └── test_engine.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example            # 环境变量模板
```

## 本地运行指南

本项目被设计为通过 Docker 运行，这是最简单、最可靠的方式。

### 环境准备

-   [Docker](https://www.docker.com/products/docker-desktop/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

### 操作步骤

1.  **克隆项目**
    ```bash
    git clone <your-repo-url>
    cd <project-directory>
    ```

2.  **创建并配置环境变量文件 (`.env`)**
    -   将 `.env.example` 文件复制一份，并重命名为 `.env`。
        ```bash
        cp .env.example .env
        ```
    -   打开 `.env` 文件。对于大部分公开数据的获取，您**无需**填写API密钥。但对于某些特定功能（如DEX数据），可能需要配置RPC URL。
        -   `RPC_URL_ETHEREUM`: (可选) 您的以太坊主网 RPC URL。
        -   `BINANCE_API_KEY`, `OKX_API_KEY` 等: (可选) 如果您需要使用交易所的私有API（例如，未来开发交易功能），可以在此配置。**注意：变量名需要大写，例如 `OKX_API_KEY`**。

3.  **启动应用**
    -   在项目根目录下，运行以下命令来构建并启动所有服务：
        ```bash
        docker-compose up --build
        ```
    -   第一次启动时，`--build` 参数会构建镜像，可能需要几分钟。

4.  **访问应用**
    -   打开浏览器，访问 `http://localhost:8501`。

## 如何运行测试

测试套件用于验证核心业务逻辑的正确性。

1.  **安装测试依赖**
    ```bash
    pip install pytest pytest-asyncio
    ```
2.  **运行测试**
    -   确保您位于项目根目录 (`code-feat-production-grade-upgrade`) 的上一级目录。
    -   运行以下命令。`PYTHONPATH` 的设置是为了确保测试脚本能正确找到项目模块。
    ```bash
    PYTHONPATH=$PYTHONPATH:code-feat-production-grade-upgrade python3 -m pytest
    ```

## 配置文件说明

### `.env` 文件
存储所有敏感信息和环境特定的配置。`config.py` 会自动加载这些变量。

### `fees.yml` 文件
用于配置套利引擎计算时所使用的交易手续费。

### `qualitative_data.yml` 文件
一个手动维护的数据库，用于存储无法通过API直接获取的交易所信息。您可以直接编辑此文件来更新、修正或添加信息。
