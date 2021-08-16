# MyStrategyNew2
# Author: @ntsd (Jirawat Boonkumnerd)
# Github: https://github.com/ntsd
# V2 Update: Add periods for each timeframe
# V3 Update: Add operators
# V4 Update: Optimise hyperops remove 30m and 4h
# freqtrade download-data --exchange binance -t 5m --days 500
# freqtrade download-data --exchange binance -t 15m --days 500
# freqtrade download-data --exchange binance -t 30m --days 500
# freqtrade download-data --exchange binance -t 1h --days 500
# freqtrade download-data --exchange binance -t 4h --days 500
# ShortTradeDurHyperOptLoss, SharpeHyperOptLoss, SharpeHyperOptLossDaily, OnlyProfitHyperOptLoss
# freqtrade hyperopt --hyperopt-loss OnlyProfitHyperOptLoss --spaces buy sell --timeframe 5m -e 2000 --timerange 20210301-20210813 --strategy MyStrategyNew4
# freqtrade backtesting --timeframe 5m --timerange 20200807-20210807 --strategy MyStrategyNew

from freqtrade.strategy import IStrategy, CategoricalParameter, DecimalParameter, IntParameter, merge_informative_pair
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce
import numpy as np

# Timeframes available for the exchange `Binance`: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
timeframes = ['5m', '15m', '1h']
base_timeframe = timeframes[0]
info_timeframes = timeframes[1:]


def greater_operator(dataframe: DataFrame, first_indicator: str, second_indicator: str):
    return (dataframe[first_indicator] >
            dataframe[second_indicator])


def true_operator(dataframe: DataFrame, first_indicator: str, second_indicator: str):
    return (dataframe['volume'] > 10)


operators = {
    '>': greater_operator,
    'D': true_operator
}


class MyStrategyNew4(IStrategy):
    # ROI table:
    minimal_roi = {"0": 1}

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.15
    trailing_stop_positive_offset = 0.197
    trailing_only_offset_is_reached = True

    # Stoploss
    stoploss = -1

    # Timeframe
    timeframe = base_timeframe

    # Hyperopt parameters
    buy_fast_period_5m = IntParameter(5, 50, default=12, space='buy')
    buy_slow_period_5m = IntParameter(5, 50, default=26, space='buy')
    buy_operator_5m = CategoricalParameter(operators.keys(), space='buy')
    sell_fast_period_5m = IntParameter(5, 50, default=12, space='sell')
    sell_slow_period_5m = IntParameter(5, 50, default=26, space='sell')
    sell_operator_5m = CategoricalParameter(operators.keys(), space='sell')

    buy_fast_period_15m = IntParameter(5, 50, default=12, space='buy')
    buy_slow_period_15m = IntParameter(5, 50, default=26, space='buy')
    buy_operator_15m = CategoricalParameter(operators.keys(), space='buy')
    sell_fast_period_15m = IntParameter(5, 50, default=12, space='sell')
    sell_slow_period_15m = IntParameter(5, 50, default=26, space='sell')
    sell_operator_15m = CategoricalParameter(operators.keys(), space='sell')

    buy_fast_period_1h = IntParameter(5, 50, default=12, space='buy')
    buy_slow_period_1h = IntParameter(5, 50, default=26, space='buy')
    buy_operator_1h = CategoricalParameter(operators.keys(), space='buy')
    sell_fast_period_1h = IntParameter(5, 50, default=12, space='sell')
    sell_slow_period_1h = IntParameter(5, 50, default=26, space='sell')
    sell_operator_1h = CategoricalParameter(operators.keys(), space='sell')

    def apply_indicator(self, dataframe: DataFrame, key: str, period: int):
        if key not in dataframe.keys():
            dataframe[key] = ta.EMA(dataframe, timeperiod=period)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."

        runmode = self.dp.runmode.value
        periods = set()
        if runmode in ('backtest', 'live', 'dry_run'):
            periods.add(self.buy_fast_period_5m.value)
            periods.add(self.buy_slow_period_5m.value)
            periods.add(self.sell_fast_period_5m.value)
            periods.add(self.sell_slow_period_5m.value)
            for info_timeframe in info_timeframes:
                periods.add(getattr(self, f'buy_fast_period_{info_timeframe}').value)
                periods.add(getattr(self, f'buy_slow_period_{info_timeframe}').value)
                periods.add(getattr(self, f'sell_fast_period_{info_timeframe}').value)
                periods.add(getattr(self, f'sell_slow_period_{info_timeframe}').value)
        else:
            for period in self.buy_fast_period_5m.range:
                periods.add(period)

        for info_timeframe in info_timeframes:
            info_dataframe = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=info_timeframe)
            for period in periods:
                self.apply_indicator(info_dataframe, f'ema_{period}', period)
            dataframe = merge_informative_pair(dataframe, info_dataframe, self.timeframe, info_timeframe, ffill=True)

        for period in periods:
            self.apply_indicator(dataframe, f'ema_{period}', period)

        return dataframe

    def info_timeframe_condition(self, dataframe, fast_indicator, slow_indicator, operator, info_timeframe):
        condition = operators[operator](
            dataframe, f'{fast_indicator}_{info_timeframe}', f'{slow_indicator}_{info_timeframe}')
        return condition, dataframe

    def base_timeframe_condition(self, dataframe, fast_indicator, slow_indicator, operator):
        condition = operators[operator](dataframe, fast_indicator, slow_indicator)
        return condition, dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast_period = self.buy_fast_period_5m.value
        slow_period = self.buy_slow_period_5m.value
        operator = self.buy_operator_5m.value

        conditions = list()

        fast_indicator = f'ema_{fast_period}'
        slow_indicator = f'ema_{slow_period}'
        condition, dataframe = self.base_timeframe_condition(dataframe, fast_indicator, slow_indicator, operator)
        conditions.append(condition)

        for info_timeframe in info_timeframes:
            fast_period_timeframe = getattr(self, f'buy_fast_period_{info_timeframe}').value
            slow_period_timeframe = getattr(self, f'buy_slow_period_{info_timeframe}').value
            operator_timeframe = getattr(self, f'buy_operator_{info_timeframe}').value

            if operator_timeframe == 'D':
                continue

            fast_indicator_timeframe = f'ema_{fast_period_timeframe}'
            slow_indicator_timeframe = f'ema_{slow_period_timeframe}'

            condition, dataframe = self.info_timeframe_condition(
                dataframe, fast_indicator_timeframe, slow_indicator_timeframe, operator_timeframe, info_timeframe)
            conditions.append(condition)

        dataframe.loc[reduce(lambda x, y: x & y, conditions), 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast_period = self.sell_fast_period_5m.value
        slow_period = self.sell_slow_period_5m.value
        operator = self.sell_operator_5m.value

        conditions = list()

        fast_indicator = f'ema_{fast_period}'
        slow_indicator = f'ema_{slow_period}'
        condition, dataframe = self.base_timeframe_condition(dataframe, fast_indicator, slow_indicator, operator)
        conditions.append(condition)

        for info_timeframe in info_timeframes:
            fast_period_timeframe = getattr(self, f'sell_fast_period_{info_timeframe}').value
            slow_period_timeframe = getattr(self, f'sell_slow_period_{info_timeframe}').value
            operator_timeframe = getattr(self, f'sell_operator_{info_timeframe}').value

            if operator_timeframe == 'D':
                continue

            fast_indicator_timeframe = f'ema_{fast_period_timeframe}'
            slow_indicator_timeframe = f'ema_{slow_period_timeframe}'

            condition, dataframe = self.info_timeframe_condition(
                dataframe, fast_indicator_timeframe, slow_indicator_timeframe, operator_timeframe, info_timeframe)
            conditions.append(condition)

        dataframe.loc[reduce(lambda x, y: x & y, conditions), 'sell'] = 1

        return dataframe
