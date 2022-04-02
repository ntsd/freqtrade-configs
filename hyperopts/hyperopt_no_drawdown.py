"""
ProfitDrawDownHyperOptLoss

This module defines the alternative HyperOptLoss class based on Profit &
Drawdown objective which can be used for Hyperoptimization.

Possible to change `DRAWDOWN_MULT` to penalize drawdown objective for
individual needs.
"""
from datetime import datetime

import numpy as np
from pandas import DataFrame

from freqtrade.optimize.hyperopt import IHyperOptLoss


class NoDrawDownHyperOptLoss(IHyperOptLoss):
    @staticmethod
    def hyperopt_loss_function(results: DataFrame, trade_count: int,
                               min_date: datetime, max_date: datetime,
                               *args, **kwargs) -> float:
        profit_abs = results["profit_abs"]
    
        if profit_abs.lt(0).any().any():
            return 0

        total_profit = results["profit_ratio"]
        days_period = (max_date - min_date).days

        # adding slippage of 0.1% per trade
        total_profit = total_profit - 0.0005
        expected_returns_mean = total_profit.sum() / days_period
        up_stdev = np.std(total_profit)

        if up_stdev != 0:
            sharp_ratio = expected_returns_mean / up_stdev * np.sqrt(365)
        else:
            # Define high (negative) sharpe ratio to be clear that this is NOT optimal.
            sharp_ratio = -20.

        # print(expected_returns_mean, up_stdev, sharp_ratio)
        return -sharp_ratio
