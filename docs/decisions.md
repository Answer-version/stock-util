# Architecture Decisions

- Phase 1 is intentionally crypto daily only.
- The canonical market data shape is `MultiIndex[datetime, symbol]`.
- Daily backtests use signal-at-close and execute-at-next-open semantics.
