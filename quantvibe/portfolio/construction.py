from __future__ import annotations

import pandas as pd


def top_n_equal_weight(score_wide: pd.DataFrame, top_n: int) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=score_wide.index, columns=score_wide.columns)
    for timestamp, row in score_wide.iterrows():
        valid = row.dropna().sort_values(ascending=False)
        selected = valid.head(top_n).index
        if len(selected) == 0:
            continue
        weights.loc[timestamp, selected] = 1.0 / len(selected)
    return weights
