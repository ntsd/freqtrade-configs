# TODO Strategy
# Author: @ntsd (Jirawat Boonkumnerd)
# github: https://github.com/ntsd

from freqtrade.strategy import IStrategy, CategoricalParameter
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce
import numpy as np

time_periods = range(1, 20)

indicators = set()
indicators = {'SMA', 'EMA'}
indicators_with_timeperiod = list()
for indicator in indicators:
    for timeperiod in time_periods:
        indicators_with_timeperiod.append(f'{indicator}-{timeperiod}')

def ta_apply(dataframe, indicator):
    if indicator in dataframe.keys():
        return dataframe[indicator]

class ActionZone3Strategy(IStrategy):
    # ROI table:
    minimal_roi = {
        "0": 0.06,
        "33": 0.044,
        "56": 0.023
    }

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.209
    trailing_stop_positive_offset = 0.293
    trailing_only_offset_is_reached = False

    # Stoploss:
    stoploss = -1
    # Buy hypers
    timeframe = '5m'

    buy_indicator0 = CategoricalParameter(indicators_with_timeperiod, space='buy')
    buy_indicator1 = CategoricalParameter(indicators_with_timeperiod, space='buy')

    sell_indicator0 = CategoricalParameter(indicators_with_timeperiod, space='sell')
    sell_indicator1 = CategoricalParameter(indicators_with_timeperiod, space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
