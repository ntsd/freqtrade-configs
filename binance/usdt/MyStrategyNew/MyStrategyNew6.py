# MyStrategyNew6
# Author: @ntsd (Jirawat Boonkumnerd)
# Github: https://github.com/ntsd
# V2 Update: Add periods for each timeframe
# V3 Update: Add operators
# V6 Update: Optimise by categories
# freqtrade download-data --exchange binance -t 5m --days 500
# freqtrade download-data --exchange binance -t 15m --days 500
# freqtrade download-data --exchange binance -t 30m --days 500
# freqtrade download-data --exchange binance -t 1h --days 500
# freqtrade download-data --exchange binance -t 4h --days 500
# ShortTradeDurHyperOptLoss, SharpeHyperOptLoss, SharpeHyperOptLossDaily, OnlyProfitHyperOptLoss
# freqtrade hyperopt --hyperopt-loss OnlyProfitHyperOptLoss --spaces buy sell --timeframe 5m -e 2000 --timerange 20210301-20210813 --strategy MyStrategyNew6
# freqtrade backtesting --timeframe 5m --timerange 20200807-20210807 --strategy MyStrategyNew6

from typing import Tuple
from freqtrade.strategy import IStrategy, CategoricalParameter, DecimalParameter, IntParameter, merge_informative_pair
from pandas import DataFrame, Series

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce
import numpy as np
import itertools

########################### Static Parameters ###########################

# Timeframes available for the exchange `Binance`: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
TIMEFRAMES = ('5m', '15m', '30m', '1h', '4h')
BASE_TIMEFRAME = TIMEFRAMES[0]
INFO_TIMEFRAMES = TIMEFRAMES[1:]

PERIODS = (5, 8, 13, 24, 39, 48) # (5, 6, 8, 9, 13, 18, 24, 31, 39, 48)
MAX_CONDITIONS = 5

########################### Operators ###########################


def greater_operator(dataframe: DataFrame, first_indicator: str, second_indicator: str):
    return (dataframe[first_indicator] >
            dataframe[second_indicator])


OPERATORS = {
    '>': greater_operator
}


def apply_operator(dataframe: DataFrame, first_indicator, second_indicator, operator) -> tuple[Series, DataFrame]:
    condition = OPERATORS[operator](dataframe, first_indicator, second_indicator)
    return condition, dataframe

########################### Condition ###########################


def generate_condition_set() -> set:
    """ generate_condition_set wil return possible indicators with operator
        {indicator_with_period}-{operator}-{indicator_with_period}
        None condition mean do nothing
    """
    # indicators_with_period will be format {indicator_name}_{period}_{timeframe}
    indicator_with_periods = set()
    for timeframe in TIMEFRAMES:
        for periods in PERIODS:
            indicator_with_periods.add(f'ema_{periods}_{timeframe}')

    # indicator_with_operators will be format {indicator_with_period}-{operator}-{indicator_with_period}
    possible_condition = set()
    possible_condition.add('None')
    indicators_permutations = itertools.permutations(indicator_with_periods, 2)
    for first_indicator, second_indicator in indicators_permutations:
        for operator in OPERATORS:
            possible_condition.add(f'{first_indicator}-{operator}-{second_indicator}')

    return possible_condition


def unpack_condition(condition: str) -> tuple[str, str, str]:
    """ Return first_indicator, operator, second_indicator"""
    if condition == 'None':
        return None, None, None
    first_indicator, operator, second_indicator = condition.split('-')
    return first_indicator, operator, second_indicator


condition_set = generate_condition_set()
print('condition_set legth:', len(condition_set))


class MyStrategyNew6(IStrategy):
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
    timeframe = BASE_TIMEFRAME

    # Hyperopt parameters
    buy_condition_0 = CategoricalParameter(condition_set, space='buy')
    buy_condition_1 = CategoricalParameter(condition_set, space='buy')
    buy_condition_2 = CategoricalParameter(condition_set, space='buy')

    sell_condition_0 = CategoricalParameter(condition_set, space='sell')
    sell_condition_1 = CategoricalParameter(condition_set, space='sell')
    sell_condition_2 = CategoricalParameter(condition_set, space='sell')

    def apply_indicator(self, dataframe: DataFrame, key: str, period: int):
        if key not in dataframe.keys():
            dataframe[key] = ta.EMA(dataframe, timeperiod=period)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."

        avalidable_info_timeframes = set()
        avalidable_periods = set()

        run_mode = self.dp.runmode.value
        if run_mode in ('backtest', 'live', 'dry_run'):
            # TODO add only using timeframe and period
            pass
        else:
            avalidable_info_timeframes = INFO_TIMEFRAMES
            avalidable_periods = PERIODS

        # apply info timeframe indicator
        for info_timeframe in avalidable_info_timeframes:
            info_dataframe = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=info_timeframe)
            for period in avalidable_periods:
                self.apply_indicator(info_dataframe, f'ema_{period}', period)
            dataframe = merge_informative_pair(dataframe, info_dataframe, self.timeframe, info_timeframe, ffill=True)

        # apply base timeframe indicator
        for period in avalidable_periods:
            self.apply_indicator(dataframe, f'ema_{period}_{BASE_TIMEFRAME}', period)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = list()

        for condition_idx in range(MAX_CONDITIONS):
            condition_name = getattr(self, f'buy_condition_{condition_idx}').value
            first_indicator, operator, second_indicator = unpack_condition(condition_name)
            condition, dataframe = apply_operator(dataframe, first_indicator, second_indicator, operator)
            conditions.append(condition)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = list()

        for condition_idx in range(MAX_CONDITIONS):
            condition_name = getattr(self, f'sell_condition_{condition_idx}').value
            first_indicator, operator, second_indicator = unpack_condition(condition_name)
            condition, dataframe = apply_operator(dataframe, first_indicator, second_indicator, operator)
            conditions.append(condition)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), 'sell'] = 1

        return dataframe
