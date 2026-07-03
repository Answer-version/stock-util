from __future__ import annotations

from datetime import date
from io import BytesIO, StringIO
from typing import Any

from quantvibe.core.exceptions import DataSourceUnavailable
from quantvibe.backtest.engine import BacktestEngine
from quantvibe.backtest.report import (
    build_backtest_export_frame,
    build_drawdown_frame,
    build_equity_frame,
    build_holdings_frame,
    build_latest_scores_frame,
    build_metrics_frame,
    build_normalized_price_frame,
    build_turnover_frame,
)
from quantvibe.core.config import load_config
from quantvibe.data.cache import DataCache
from quantvibe.data.registry import get_provider
from quantvibe.factors.composite import FactorComposite
from quantvibe.factors.technical import MAGapFactor, MomentumFactor, RSI14Factor, VolatilityFactor, VolumeRatioFactor
from quantvibe.pipelines.research import ResearchPipeline, ResearchRun
from quantvibe.ui.theme import APP_CSS


TODAY = date.today()
DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
DEFAULT_START_DATE = date(TODAY.year, 1, 1)
DEFAULT_END_DATE = TODAY
DEFAULT_TOP_N = 1
FACTOR_PACK = [
    MomentumFactor(),
    VolatilityFactor(),
    RSI14Factor(),
    MAGapFactor(),
    VolumeRatioFactor(),
]
FACTOR_LABELS = {
    "momentum_20": "20日动量",
    "volatility_20": "20日波动率",
    "rsi_14": "RSI(14)",
    "ma_gap_5_20": "5/20日均线偏离",
    "volume_ratio_20": "20日量比",
}


def _imports() -> tuple[Any, Any, Any]:
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import streamlit as st
    except ImportError as exc:
        raise SystemExit(
            "仪表盘依赖 streamlit 和 plotly，请先安装 requirements.txt。"
        ) from exc
    return st, px, go


def _build_pipeline() -> ResearchPipeline:
    config = load_config()
    cache = DataCache(config["data"]["cache_dir"])
    provider = get_provider(
        config["providers"]["crypto"]["default"],
        exchange_id=config["providers"]["crypto"]["exchange_id"],
        cache=cache,
        cache_ttl_seconds=config["providers"]["crypto"]["cache_ttl_seconds"],
    )
    composite = FactorComposite(factors=FACTOR_PACK)
    engine = BacktestEngine(
        periods_per_year=365,
        default_commission_bps=float(config["backtest"]["commission_bps"]),
        default_slippage_bps=float(config["backtest"]["slippage_bps"]),
    )
    return ResearchPipeline(provider=provider, composite=composite, engine=engine)


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _render_metric_card(st: Any, label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_header(st: Any) -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-kicker">QuantVibe 第二阶段</div>
          <h1 class="hero-title">中文因子研究面板</h1>
          <p class="hero-subtitle">
            用一个研究仪表盘把加密日频数据、横截面因子、Top N 组合和回测结果串起来。
            当前版本聚焦最稳的闭环：多币种、技术因子、下一根开盘成交、图形化结果回看。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _sidebar_controls(st: Any) -> dict[str, Any]:
    with st.sidebar:
        st.markdown("## 研究参数")
        st.caption("默认参数使用已验证的轻量真实数据组合，首次上手更稳。")
        symbol_text = st.text_area(
            "标的池",
            value=", ".join(DEFAULT_SYMBOLS),
            help="用英文逗号分隔，例如 BTC/USDT, ETH/USDT, SOL/USDT, BNB/USDT",
        )
        start_date = st.date_input("开始日期", value=DEFAULT_START_DATE)
        end_date = st.date_input("结束日期", value=DEFAULT_END_DATE)
        top_n = st.slider("持仓数量 Top N", min_value=1, max_value=6, value=DEFAULT_TOP_N)
        factor_names = [factor.name for factor in FACTOR_PACK]
        selected_factors = st.multiselect(
            "启用因子",
            factor_names,
            default=factor_names,
            format_func=lambda name: FACTOR_LABELS.get(name, name),
        )
        run = st.button("运行可视化回测", type="primary", width="stretch")
        st.markdown("---")
        st.caption("执行规则：收盘生成信号，下一根开盘成交。")
        return {
            "symbols": [item.strip().upper() for item in symbol_text.split(",") if item.strip()],
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "top_n": top_n,
            "selected_factors": selected_factors,
            "run": run,
        }


def _select_pipeline(selected_factors: list[str]) -> ResearchPipeline:
    pipeline = _build_pipeline()
    pipeline.composite = FactorComposite([factor for factor in FACTOR_PACK if factor.name in selected_factors])
    return pipeline


def _build_equity_figure(px: Any, run: ResearchRun):
    equity_frame = build_equity_frame(run)
    fig = px.line(equity_frame, x="datetime", y="equity_curve", template="plotly_white")
    fig.update_traces(line=dict(color="#006d5b", width=3))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def _build_drawdown_figure(px: Any, run: ResearchRun):
    drawdown_frame = build_drawdown_frame(run)
    fig = px.area(drawdown_frame, x="datetime", y="drawdown", template="plotly_white")
    fig.update_traces(line=dict(color="#d76f30", width=2), fillcolor="rgba(215,111,48,0.28)")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis_tickformat=".0%")
    return fig


def _build_price_figure(px: Any, run: ResearchRun):
    prices = build_normalized_price_frame(run)
    fig = px.line(prices, x="datetime", y="normalized_price", color="symbol", template="plotly_white")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
    return fig


def _build_turnover_figure(px: Any, run: ResearchRun):
    turnover = build_turnover_frame(run)
    fig = px.bar(turnover, x="datetime", y="turnover", template="plotly_white")
    fig.update_traces(marker_color="#3f7aa8")
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def _build_factor_figure(px: Any, run: ResearchRun):
    scores = build_latest_scores_frame(run)
    fig = px.density_heatmap(
        scores,
        x="datetime",
        y="symbol",
        z="score",
        color_continuous_scale=["#f0e7d8", "#d76f30", "#006d5b"],
        template="plotly_white",
    )
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def _build_holdings_figure(px: Any, run: ResearchRun):
    holdings = build_holdings_frame(run)
    if holdings.empty:
        return None
    fig = px.area(holdings, x="datetime", y="weight", color="symbol", template="plotly_white")
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_tickformat=".0%")
    return fig


def _build_export_payloads(run: ResearchRun, figures: dict[str, Any]) -> dict[str, bytes | str]:
    csv_frame = build_backtest_export_frame(run)
    csv_buffer = StringIO()
    csv_frame.to_csv(csv_buffer, index=False)

    metrics_html = build_metrics_frame(run).to_html(index=False, border=0, classes="metrics-table")
    holdings_html = build_holdings_frame(run).to_html(index=False, border=0, classes="holdings-table")
    price_html = run.prices.reset_index().tail(120).to_html(index=False, border=0, classes="price-table")
    report_html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>QuantVibe 回测报告</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif; margin: 32px; color: #1d1a16; background: #f7f1e8; }}
          h1, h2 {{ margin-bottom: 8px; }}
          .section {{ margin-bottom: 28px; padding: 18px 20px; background: #fff9f1; border-radius: 18px; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 8px 10px; border-bottom: 1px solid rgba(29,26,22,0.08); text-align: left; }}
        </style>
      </head>
      <body>
        <h1>QuantVibe 回测报告</h1>
        <p>标的池：{", ".join(sorted(run.prices.index.get_level_values("symbol").unique()))}</p>
        <div class="section">
          <h2>核心指标</h2>
          {metrics_html}
        </div>
        <div class="section">
          <h2>净值曲线</h2>
          {figures["equity"].to_html(full_html=False, include_plotlyjs="cdn")}
        </div>
        <div class="section">
          <h2>回撤曲线</h2>
          {figures["drawdown"].to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="section">
          <h2>价格相对强弱</h2>
          {figures["price"].to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="section">
          <h2>综合得分热力图</h2>
          {figures["factor"].to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="section">
          <h2>最新持仓明细</h2>
          {holdings_html}
        </div>
        <div class="section">
          <h2>价格样本</h2>
          {price_html}
        </div>
      </body>
    </html>
    """

    png_buffer = BytesIO()
    figures["equity"].write_image(png_buffer, format="png", scale=2)

    return {
        "csv": csv_buffer.getvalue(),
        "html": report_html,
        "png": png_buffer.getvalue(),
    }


def _render_export_bar(st: Any, payloads: dict[str, bytes | str]) -> None:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">结果导出</div><div class="section-copy">支持导出回测时序 CSV、净值图 PNG 和完整 HTML 报告。</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    with cols[0]:
        st.download_button(
            "导出回测 CSV",
            data=payloads["csv"],
            file_name="quantvibe_backtest.csv",
            mime="text/csv",
            width="stretch",
        )
    with cols[1]:
        st.download_button(
            "导出净值图 PNG",
            data=payloads["png"],
            file_name="quantvibe_equity_curve.png",
            mime="image/png",
            width="stretch",
        )
    with cols[2]:
        st.download_button(
            "导出 HTML 报告",
            data=payloads["html"],
            file_name="quantvibe_report.html",
            mime="text/html",
            width="stretch",
        )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_overview(st: Any, run: ResearchRun, equity_fig: Any, drawdown_fig: Any) -> None:
    metrics = run.backtest.metrics
    metric_cols = st.columns(4)
    with metric_cols[0]:
        _render_metric_card(st, "总收益", _format_pct(metrics["total_return"]), "策略区间复合收益")
    with metric_cols[1]:
        _render_metric_card(st, "夏普比率", f"{metrics['sharpe']:.2f}", "单位波动下的风险收益质量")
    with metric_cols[2]:
        _render_metric_card(st, "最大回撤", _format_pct(metrics["max_drawdown"]), "从峰值回落的最大幅度")
    with metric_cols[3]:
        _render_metric_card(st, "胜率", _format_pct(metrics["win_rate"]), "样本期内正收益周期占比")

    left, right = st.columns([1.25, 0.95])
    with left:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">净值曲线</div><div class="section-copy">累计净值和每期收益联动展示。</div>', unsafe_allow_html=True)
        st.plotly_chart(equity_fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">回撤曲线</div><div class="section-copy">回撤区域能快速看出策略最难熬的区间。</div>', unsafe_allow_html=True)
        st.plotly_chart(drawdown_fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_market_tab(st: Any, run: ResearchRun, price_fig: Any, turnover_fig: Any) -> None:
    left, right = st.columns([1.1, 1.1])
    with left:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">价格相对强弱</div><div class="section-copy">把标的价格拉到同一起跑线，方便看相对强弱。</div>', unsafe_allow_html=True)
        st.plotly_chart(price_fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">换手节奏</div><div class="section-copy">观察组合切换节奏，避免被高换手吞掉收益。</div>', unsafe_allow_html=True)
        st.plotly_chart(turnover_fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_factor_tab(st: Any, factor_fig: Any) -> None:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">综合得分热力图</div><div class="section-copy">最近 20 个交易日的横截面综合得分热力图。</div>', unsafe_allow_html=True)
    st.plotly_chart(factor_fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_holdings_tab(st: Any, run: ResearchRun, holdings_fig: Any) -> None:
    left, right = st.columns([1.1, 0.9])
    holdings = build_holdings_frame(run)
    with left:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">持仓轮动</div><div class="section-copy">等权 Top N 持仓随时间的切换轨迹。</div>', unsafe_allow_html=True)
        if holdings.empty:
            st.info("当前参数下没有生成持仓。")
        else:
            st.plotly_chart(holdings_fig, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">最新持仓</div><div class="section-copy">方便快速看最后一期持仓结果。</div>', unsafe_allow_html=True)
        if holdings.empty:
            st.info("没有持仓数据。")
        else:
            latest_dt = holdings["datetime"].max()
            latest = holdings[holdings["datetime"] == latest_dt].sort_values("weight", ascending=False)
            latest["weight"] = latest["weight"].map(lambda value: f"{value * 100:.2f}%")
            st.dataframe(latest, width="stretch", hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)


def _render_data_tab(st: Any, run: ResearchRun) -> None:
    price_tab, score_tab = st.tabs(["价格面板", "得分面板"])
    with price_tab:
        st.dataframe(run.prices.reset_index().tail(200), width="stretch", hide_index=True)
    with score_tab:
        st.dataframe(run.scores.reset_index(name="score").tail(200), width="stretch", hide_index=True)


def main() -> None:
    st, px, _go = _imports()
    st.set_page_config(page_title="QuantVibe 中文因子面板", page_icon="Q", layout="wide")
    _render_header(st)
    controls = _sidebar_controls(st)

    if not controls["run"]:
        st.info("配置左侧参数后点击“运行可视化回测”，即可生成图形化研究结果。")
        return
    if not controls["selected_factors"]:
        st.warning("至少启用一个因子。")
        return
    if not controls["symbols"]:
        st.warning("至少输入一个交易对。")
        return

    pipeline = _select_pipeline(controls["selected_factors"])
    try:
        with st.spinner("正在拉取行情、计算因子并生成图表..."):
            run = pipeline.run_full(
                symbols=controls["symbols"],
                start=controls["start"],
                end=controls["end"],
                top_n=controls["top_n"],
            )
    except DataSourceUnavailable as exc:
        st.error("实时行情源当前不可用，系统已尝试主数据源与备用真实交易所接口，但这次仍未成功。")
        st.info("你可以稍后重试，或者先缩短日期范围、减少标的数量后再运行。")
        st.caption(f"错误详情：{exc}")
        return

    equity_fig = _build_equity_figure(px, run)
    drawdown_fig = _build_drawdown_figure(px, run)
    price_fig = _build_price_figure(px, run)
    turnover_fig = _build_turnover_figure(px, run)
    factor_fig = _build_factor_figure(px, run)
    holdings_fig = _build_holdings_figure(px, run)
    export_payloads = _build_export_payloads(
        run,
        {
            "equity": equity_fig,
            "drawdown": drawdown_fig,
            "price": price_fig,
            "factor": factor_fig,
        },
    )
    _render_export_bar(st, export_payloads)

    overview_tab, market_tab, factor_tab, holdings_tab, data_tab = st.tabs(
        ["总览", "市场视角", "因子视角", "持仓明细", "原始数据"]
    )
    with overview_tab:
        _render_overview(st, run, equity_fig, drawdown_fig)
    with market_tab:
        _render_market_tab(st, run, price_fig, turnover_fig)
    with factor_tab:
        _render_factor_tab(st, factor_fig)
    with holdings_tab:
        _render_holdings_tab(st, run, holdings_fig)
    with data_tab:
        _render_data_tab(st, run)
