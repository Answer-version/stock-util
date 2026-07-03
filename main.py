from __future__ import annotations

import argparse

from quantvibe.backtest.engine import BacktestEngine
from quantvibe.core.config import load_config
from quantvibe.data.cache import DataCache
from quantvibe.data.registry import get_provider
from quantvibe.factors.composite import FactorComposite
from quantvibe.factors.technical import MAGapFactor, MomentumFactor, RSI14Factor, VolatilityFactor, VolumeRatioFactor
from quantvibe.pipelines.research import ResearchPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QuantVibe Phase 1 CLI")
    parser.add_argument("--symbols", nargs="+", required=True, help="Canonical symbols, e.g. BTC/USDT ETH/USDT")
    parser.add_argument("--start", required=True, help="UTC start date, e.g. 2024-01-01")
    parser.add_argument("--end", help="UTC end date")
    parser.add_argument("--top-n", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config()
    cache = DataCache(config["data"]["cache_dir"])
    provider = get_provider(
        config["providers"]["crypto"]["default"],
        exchange_id=config["providers"]["crypto"]["exchange_id"],
        cache=cache,
        cache_ttl_seconds=config["providers"]["crypto"]["cache_ttl_seconds"],
    )
    composite = FactorComposite(
        factors=[
            MomentumFactor(),
            VolatilityFactor(),
            RSI14Factor(),
            MAGapFactor(),
            VolumeRatioFactor(),
        ]
    )
    engine = BacktestEngine(
        periods_per_year=365,
        default_commission_bps=float(config["backtest"]["commission_bps"]),
        default_slippage_bps=float(config["backtest"]["slippage_bps"]),
    )
    pipeline = ResearchPipeline(provider=provider, composite=composite, engine=engine)
    result = pipeline.run(
        symbols=args.symbols,
        start=args.start,
        end=args.end,
        top_n=args.top_n or int(config["backtest"]["top_n"]),
    )
    print(result.metrics)


if __name__ == "__main__":
    main()
