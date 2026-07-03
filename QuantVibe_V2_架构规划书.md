# QuantVibe V2 架构规划书

文档用途：交付给 AI 编程助手作为可直接实施的开发蓝图。  
目标：先构建一个“可验证、可扩展、不自带未来函数”的多资产量化选股研究系统。

## 一、产品定位

### 1.1 核心目标

构建一个支持 A 股 / 美股 / 加密货币的研究型量化选股工具，覆盖：

- 多标的行情获取
- 因子计算
- 横截面打分
- 组合构建
- 回测评估
- 每日/定时信号输出

### 1.2 非目标

- 不做实盘交易
- 不做券商下单
- 不做复杂前端 GUI
- 不在 V1 引入高频撮合级仿真
- 不承诺免费数据可满足生产级 SLA

### 1.3 V1 成功标准

V1 不是“能拉单个标的数据”，而是：

1. 能对一个标的池做横截面因子打分
2. 能生成 Top N 持仓
3. 能按严格时点规则回测
4. 能输出稳定、可复现的绩效结果

## 二、必须修正的架构原则

### 2.1 以“多标的横截面”作为核心数据模型

选股系统的最小闭环不是 `symbol -> factor -> pnl`，而是：

`universe -> panel data -> cross-sectional factors -> ranking -> portfolio -> backtest`

因此 V2 不再以单标的 `get_price(symbol)` 作为唯一主接口，而是以“批量拉取 + 标准化面板数据”为核心。

### 2.2 所有研究结果必须满足 Point-in-Time

任何因子、基本面、行业分类、成分股列表、停牌状态，都必须遵守“当时是否已知”原则。

禁止：

- 用今天的股票池回测过去
- 用财报披露后数据填充披露前日期
- 用未来 bar 的价格做当前 bar 的交易决策

### 2.3 明确区分“研究层异常”和“调度层容错”

Provider 不应默默吞掉错误返回 `None`。  
研究系统要优先保证结果可信，而不是“尽量跑完”。

规则：

- 底层 Provider 出错：抛明确异常
- 上层任务编排：决定是否降级、跳过或终止
- 回测与因子层：不接受 silently wrong data

### 2.4 分阶段推进，不在 V1 一次性解决所有市场的分钟频

正确顺序：

1. 加密日频多标的闭环
2. 日频横截面因子与回测
3. A 股/美股日频
4. Point-in-time 基本面
5. 分钟频
6. Agent 编排

## 三、推荐项目结构

```text
QuantVibe/
│
├── config/
│   ├── default.yaml
│   └── local.yaml.example
│
├── main.py
├── requirements.txt
│
├── core/
│   ├── types.py               # Literal / dataclass / enum
│   ├── exceptions.py          # 自定义异常
│   ├── calendar.py            # 交易日历、时区、会话定义
│   ├── logging.py
│   └── config.py
│
├── data/
│   ├── __init__.py
│   ├── base.py                # Provider 抽象接口
│   ├── schemas.py             # 行情/基本面/股票池 schema
│   ├── validators.py          # validate_* 函数
│   ├── registry.py
│   ├── cache.py
│   ├── universe.py            # 股票池构建与快照
│   └── providers/
│       ├── crypto_ccxt.py
│       ├── a_share_akshare.py
│       ├── a_share_mootdx.py
│       ├── us_yfinance.py
│       └── us_polygon.py
│
├── factors/
│   ├── __init__.py
│   ├── base.py
│   ├── technical.py
│   ├── fundamental.py
│   ├── crypto_native.py
│   ├── preprocess.py          # winsorize/zscore/neutralize
│   └── composite.py
│
├── portfolio/
│   ├── __init__.py
│   ├── construction.py        # TopN / equal weight / risk caps
│   └── constraints.py
│
├── backtest/
│   ├── __init__.py
│   ├── engine.py
│   ├── broker.py              # 成交价格、滑点、手续费
│   ├── metrics.py
│   └── report.py
│
├── pipelines/
│   ├── research.py            # 研究型端到端流程
│   ├── daily_signal.py        # 每日信号生成
│   └── scheduled_jobs.py
│
├── notebooks/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── docs/
    └── decisions.md           # 关键架构决策记录
```

## 四、核心契约

### 4.1 类型定义

```python
FreqType = Literal["1m", "5m", "15m", "30m", "1h", "1d"]
AssetType = Literal["crypto", "a_share", "us_stock"]
PriceAdjustType = Literal["raw", "split", "qfq", "hfq"]
ExecutionPriceType = Literal["next_open", "next_close"]
```

### 4.2 行情主接口

```python
class BaseProvider(ABC):
    asset_type: AssetType
    provider_name: str

    @abstractmethod
    def get_bars(
        self,
        symbols: list[str],
        freq: FreqType,
        start: str,
        end: str | None = None,
        adjust: PriceAdjustType = "raw",
    ) -> pd.DataFrame:
        """
        返回 MultiIndex DataFrame:
        index = [datetime, symbol]
        columns = [open, high, low, close, volume]
        datetime 必须为 UTC
        symbol 必须为系统内部 canonical symbol
        """
```

说明：

- 批量接口优先，便于统一缓存、统一校验、统一回测
- 如底层源只支持单标的，可在 Provider 内部循环聚合
- 返回值必须支持横截面按日期分组

### 4.3 股票池接口

```python
class BaseProvider(ABC):
    @abstractmethod
    def get_universe(
        self,
        as_of: str,
        universe_name: str | None = None,
    ) -> pd.DataFrame:
        """
        返回当时可交易股票池快照
        columns 至少包含:
        [symbol, listed_at, delisted_at, exchange, tradable]
        """
```

说明：

- `get_symbols()` 不足以支撑严谨回测
- 必须支持“某一天的股票池快照”
- 后续可扩展行业、板块、指数成分

### 4.4 基本面接口

```python
class BaseProvider(ABC):
    def get_fundamentals(
        self,
        symbols: list[str],
        as_of: str,
        fields: list[str],
    ) -> pd.DataFrame:
        """
        返回 point-in-time 基本面数据
        columns 至少包含:
        [symbol, field, value, report_date, publish_date, available_at]
        """
```

规则：

- `available_at` 是回测能使用该值的最早时点
- 因子层只能使用 `available_at <= rebalance_time` 的数据
- 如果免费源做不到严格 point-in-time，文档必须标注“研究近似”

### 4.5 因子接口

```python
class Factor(ABC):
    name: str
    category: str
    required_columns: tuple[str, ...] = ()

    @abstractmethod
    def compute(self, panel_df: pd.DataFrame, **kwargs) -> pd.Series:
        """
        输入:
            panel_df.index = [datetime, symbol]
        输出:
            pd.Series.index = [datetime, symbol]
            pd.Series.name = factor name
        """
```

说明：

- 因子输出必须是面板式结果
- 横截面标准化不应隐含在单个因子内部，放到 `preprocess.py`
- 默认要求因子不能读取未来数据

### 4.6 组合与回测接口

```python
class BacktestEngine:
    def run(
        self,
        prices: pd.DataFrame,
        scores: pd.Series,
        rebalance_freq: str = "1D",
        top_n: int = 10,
        execution_price: ExecutionPriceType = "next_open",
        commission_model: str = "default",
        slippage_bps: float = 5.0,
    ) -> "BacktestResult":
        ...
```

关键约束：

- 信号生成时点与成交时点必须显式定义
- 默认采用“本 bar 收盘后计算，下一 bar 开盘成交”
- 若分钟频使用 `next_open`，要处理跨 session 边界

## 五、标准化 Schema

### 5.1 行情数据

`bars_df`：

- index: `MultiIndex[datetime, symbol]`
- index level 0: UTC tz-aware datetime
- index level 1: canonical symbol
- columns: `open, high, low, close, volume`

可选扩展列：

- `vwap`
- `amount`
- `open_interest`
- `funding_rate`

### 5.2 股票池快照

`universe_df`：

- `symbol`
- `asset_type`
- `exchange`
- `listed_at`
- `delisted_at`
- `tradable`
- `industry`
- `universe_name`
- `snapshot_at`

### 5.3 基本面数据

`fundamental_df`：

- `symbol`
- `field`
- `value`
- `report_date`
- `publish_date`
- `available_at`
- `source`

## 六、时间、时区、复权规则

### 6.1 时区铁律

- 内部统一使用 UTC
- 外部源若返回本地时间，必须先 `tz_localize` 再 `tz_convert("UTC")`
- 禁止对 naive datetime 直接 `tz_convert`

### 6.2 复权规则

不同市场复权语义不同，不能混在一个默认值里。

建议：

- 加密：默认 `raw`
- 美股日频：默认 `split`
- A 股日频：默认 `qfq`
- 分钟频：优先 `raw`，若提供复权分钟线必须在文档中显式说明来源与方法

### 6.3 交易日历

必须抽象交易日历，而不是假设所有市场都按自然日连续：

- A 股：工作日且有节假日休市
- 美股：ET 交易时段，存在夏令时
- 加密：7x24

建议在 `core/calendar.py` 中统一处理：

- 下一个交易时点
- 调仓日期生成
- 会话边界判断

## 七、缓存设计

### 7.1 缓存目标

缓存是性能层，不是数据真相层。

必须保证：

- 相同请求可稳定复现
- 不同复权/不同 provider 不会串缓存
- 可追踪缓存内容的生成来源

### 7.2 推荐缓存键

```python
key = {
    "provider": "crypto_ccxt",
    "asset_type": "crypto",
    "symbols_hash": "...",
    "freq": "1d",
    "start": "2024-01-01",
    "end": "2024-12-31",
    "adjust": "raw",
    "schema_version": "v1",
}
```

不要使用过于简化的纯字符串拼接作为长期方案。

### 7.3 TTL 规则

- 日频历史老区间：可长期缓存
- 最近 1-3 个 bar：短 TTL 或增量刷新
- 分钟频：建议分块缓存，避免单文件过大

## 八、异常体系

建议定义：

```python
class QuantVibeError(Exception): ...
class DataError(QuantVibeError): ...
class DataSourceUnavailable(DataError): ...
class SchemaValidationError(DataError): ...
class RateLimitError(DataError): ...
class UnsupportedFreqError(DataError): ...
class PointInTimeViolation(DataError): ...
```

规则：

- Provider 失败应抛异常
- Pipeline 决定是否 fallback
- Notebook/CLI 层负责友好提示

不建议的规则：

- 底层统一 `return None`
- 仅打印 warning 继续回测

## 九、各市场实现建议

### 9.1 加密货币

优先级最高，适合作为 V1 首个闭环。

建议：

- 使用 `ccxt`
- 先做日频，再做分钟频
- 先支持现货主流交易对，如 `BTC/USDT`
- 若扩展资金费率/OI，拆成单独 provider，不要混进 OHLCV 主接口

注意：

- 不同交易所 symbol 语义不完全相同
- 公共 API 历史深度可能变化，不要在规划书里写死“全历史可用”

### 9.2 A 股

建议拆分为两个 Provider：

- `AShareDailyProvider`
- `AShareMinuteProvider`

原因：

- 日频与分钟频来源不同
- 复权语义不同
- 分钟线稳定性通常差于日线

另外应增加 canonical symbol 映射，例如：

- 内部：`600519.SH`
- provider A：`600519`
- provider B：`sh600519`

### 9.3 美股

建议：

- 日频先用 `yfinance`
- 分钟频单独定义为“可选增强能力”
- 若无可信分钟源，则直接在能力矩阵里标记 unsupported

不建议：

- 用 5m 数据 resample 伪造 1m 数据

## 十、因子体系建议

### 10.1 V1 因子范围

先只做价格成交量因子：

- `momentum_20`
- `volatility_20`
- `rsi_14`
- `ma_gap_5_20`
- `volume_ratio_20`

### 10.2 因子预处理必须单独显式化

不要在 `FactorComposite` 里一句 `rank(pct=True)` 就结束。

建议拆分：

1. 原始因子计算
2. 缺失值处理
3. 去极值
4. 标准化
5. 行业中性化或市值中性化
6. 加权合成

### 10.3 因子评估

V2 文档建议把以下评估指标加入因子层而不是仅放回测层：

- IC
- Rank IC
- ICIR
- 分组收益
- 覆盖率

## 十一、回测规则建议

### 11.1 V1 回测默认规则

- 调仓频率：日频每个交易日一次
- 信号时点：当日收盘后
- 成交时点：下一交易日开盘
- 持仓方式：Top N 等权
- 现金管理：未使用资金计入现金

### 11.2 成本模型

成本模型应抽象，而不是只塞两个浮点数。

建议支持：

- 百分比手续费
- 按股收费
- 最低佣金
- 滑点 bps
- 买卖双边差异

### 11.3 组合约束

V1 至少支持：

- 最大持仓数
- 单标的最大权重
- 是否允许空仓
- 最小成交额过滤

### 11.4 风险提示

分钟频策略若没有以下能力，暂不建议作为核心卖点：

- 交易时段边界处理
- 停牌/无成交处理
- 更细粒度成交模型

## 十二、配置设计

建议从单一 `config.yaml` 升级为分层配置：

- `config/default.yaml`
- `config/local.yaml`
- 环境变量覆盖敏感项

示例：

```yaml
data:
  cache_dir: ./cache
  schema_version: v1

providers:
  crypto:
    default: ccxt_binance
  a_share:
    daily: akshare
    minute: mootdx
  us_stock:
    daily: yfinance
    minute: polygon

execution:
  default_execution_price: next_open
  rebalance_freq: 1D

backtest:
  top_n: 10
  max_weight: 0.1
  slippage_bps: 5
```

## 十三、测试策略

### 13.1 单元测试

覆盖：

- schema 校验
- 时区转换
- 分页边界
- 缓存命中与失效
- 因子不使用未来数据

### 13.2 合同测试

每个 Provider 都要验证：

- 返回列完整
- index 为 UTC
- symbol 映射正确
- 空数据与异常路径行为明确

### 13.3 集成测试

联机 smoke test 可以保留，但不应是测试主体。

建议：

- CI 默认跑离线 fixture
- 手动或 nightly 跑联机测试

## 十四、阶段规划

### Phase 1：Crypto 日频 MVP

目标：

- `ccxt` 拉取多标的日频
- MultiIndex 标准化
- 缓存与 schema 校验
- 5 个技术因子
- Top N 等权回测

验收：

- 用 `BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT` 跑通完整链路

### Phase 2：研究能力增强

目标：

- 因子预处理
- IC / 分组收益
- 组合约束
- 更完整报告

### Phase 3：A 股 / 美股日频

目标：

- A 股日频接入
- 美股日频接入
- 不同市场统一日历与 symbol 规范

### Phase 4：Point-in-time 基本面

目标：

- `PE/ROE` 等基本面因子可用
- 明确近似和严格口径

### Phase 5：分钟频

目标：

- 仅在已验证数据源稳定后推进
- 优先做单市场试点，不一次铺满三市场

### Phase 6：AI Agent

目标：

- 自然语言生成研究配置
- 自动回测总结
- 提供建议但不越权修改数据口径

## 十五、给 AI 编程助手的实施规范

1. 未经允许，不要跳过 schema 校验
2. 未经定义，不要用单标的接口冒充横截面架构
3. 未经声明，不要自动 forward-fill 基本面或价格缺失
4. 未经确认，不要生成伪造的分钟线
5. 未经 point-in-time 约束，不要实现基本面回测
6. 所有外部源适配必须写明限制和降级策略
7. 每实现一个模块，先补测试再扩下一个模块

## 十六、第一条开发指令建议

建议先这样驱动 AI：

> 请按 QuantVibe V2 规划书开始实现 Phase 1。先创建目录结构，并实现 `core/types.py`、`core/exceptions.py`、`data/schemas.py`、`data/validators.py`、`data/base.py`。要求主行情接口使用 `get_bars(symbols, freq, start, end, adjust)`，返回 `MultiIndex[datetime, symbol]` 的标准化 DataFrame，并为 schema 校验编写单元测试。

## 十七、结论

V1 最容易失败的地方，不是代码写不出来，而是：

- 用单标的数据模型硬做横截面选股
- 没有明确交易时点
- 没有 point-in-time 约束
- 过早承诺分钟频全市场能力

V2 的核心思想是先把研究正确性建稳，再扩数据源和智能化层。
