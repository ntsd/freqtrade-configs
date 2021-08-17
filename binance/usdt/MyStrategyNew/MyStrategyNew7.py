# MyStrategyNew7
# Author: @ntsd (Jirawat Boonkumnerd)
# Github: https://github.com/ntsd
# V2 Update: Add periods for each timeframe
# V3 Update: Add operators
# V6 Update: Optimise by categories
# V7 Update: Optimise by using int parameter
# V7.1 Update: Remove second timeframe and second indicator to use same as first
# freqtrade download-data --exchange binance -t 5m --days 500
# freqtrade download-data --exchange binance -t 15m --days 500
# freqtrade download-data --exchange binance -t 30m --days 500
# freqtrade download-data --exchange binance -t 1h --days 500
# freqtrade download-data --exchange binance -t 4h --days 500
# ShortTradeDurHyperOptLoss, SharpeHyperOptLoss, SharpeHyperOptLossDaily, OnlyProfitHyperOptLoss
# freqtrade hyperopt --hyperopt-loss OnlyProfitHyperOptLoss --spaces buy sell --timeframe 5m -e 2000 --timerange 20210301-20210813 --strategy MyStrategyNew7
# freqtrade backtesting --timeframe 5m --timerange 20200807-20210807 --strategy MyStrategyNew7

from freqtrade.strategy import IStrategy, CategoricalParameter, IntParameter, merge_informative_pair
from pandas import DataFrame, Series

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce
import numpy as np
import itertools

########################### Static Parameters ###########################

# Timeframes available for the exchange `Binance`: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
INDICATORS = ('EMA', 'SMA', 'CCI', 'WMA', 'ROC', 'CDLLADDERBOTTOM', 'CORREL', 'MACD-0', 'MACD-1', 'MACD-2', 'STOCHRSI-0', 'STOCHRSI-1', 'HT_SINE-0')

TIMEFRAMES = ('5m', '15m', '1h')
BASE_TIMEFRAME = TIMEFRAMES[0]
INFO_TIMEFRAMES = TIMEFRAMES[1:]
TIMEFRAMES_LEN = len(TIMEFRAMES)

PERIODS = (5, 6, 8, 9, 13, 18, 24, 31, 39, 48)
PERIODS_LEN = len(PERIODS)

BUY_MAX_CONDITIONS = 4
SELL_MAX_CONDITIONS = 2

########################### Indicator ###########################


def normalize(df):
    df = (df-df.min())/(df.max()-df.min())
    return df


def apply_indicator(dataframe: DataFrame, key: str, indicator: str, period: int):
    if key in dataframe.keys():
        return

    indicator_split = indicator.split('-')
    indicator_name = indicator_split[0]
    indicator_split_len = len(indicator_split)
    if indicator_split_len == 1: # EMA-1, CCI- 1
        result = getattr(ta, indicator_name)(dataframe, timeperiod=period)
    elif indicator_split_len == 2: # MACD-1-15, # BBANDS-0-60 
        gene_index = int(indicator_split[1])
        result = getattr(ta, indicator_name)(
            dataframe,
            timeperiod=period,
        ).iloc[:, gene_index]
    dataframe[key] = normalize(result)

########################### Operators ###########################


def true_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (dataframe['volume'] > 0)


def greater_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (dataframe[main_indicator] > dataframe[crossed_indicator])


def close_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (np.isclose(dataframe[main_indicator], dataframe[crossed_indicator]))


def crossed_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (
        (qtpylib.crossed_below(dataframe[main_indicator], dataframe[crossed_indicator])) |
        (qtpylib.crossed_above(dataframe[main_indicator], dataframe[crossed_indicator]))
    )


def crossed_above_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (
        qtpylib.crossed_above(dataframe[main_indicator], dataframe[crossed_indicator])
    )


def crossed_below_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (
        qtpylib.crossed_below(dataframe[main_indicator], dataframe[crossed_indicator])
    )


OPERATORS = {
    'D': true_operator,
    '>': greater_operator,
    '=': close_operator,
    'C': crossed_operator,
    'CA': crossed_above_operator,
    # 'CB': crossed_below_operator,
}


def apply_operator(dataframe: DataFrame, first_indicator, second_indicator, operator) -> tuple[Series, DataFrame]:
    condition = OPERATORS[operator](dataframe, first_indicator, second_indicator)
    return condition, dataframe

########################### HyperOpt Parameters ###########################


def get_parameter_keys(trend: str, condition_idx: int):
    k_1 = f'{trend}_indicator_{condition_idx}'
    k_2 = f'{trend}_timeframe_{condition_idx}'
    k_3 = f'{trend}_fperiod_{condition_idx}'
    k_4 = f'{trend}_speriod_{condition_idx}'
    k_5 = f'{trend}_operator_{condition_idx}'
    return k_1, k_2, k_3, k_4, k_5


def set_hyperopt_parameters(self):
    for trend in ['buy', 'sell']:
        max_conditions = [SELL_MAX_CONDITIONS, BUY_MAX_CONDITIONS][trend == 'buy']
        for condition_idx in range(max_conditions):
            k_1, k_2, k_3, k_4, k_5 = get_parameter_keys(trend, condition_idx)
            setattr(self, k_1, CategoricalParameter(INDICATORS, space=trend))
            setattr(self, k_2, IntParameter(0, TIMEFRAMES_LEN - 1, space=trend, default=0))
            setattr(self, k_3, IntParameter(0, PERIODS_LEN - 1, space=trend, default=0))
            setattr(self, k_4, IntParameter(0, PERIODS_LEN - 1, space=trend, default=0))
            setattr(self, k_5, CategoricalParameter(OPERATORS.keys(), space=trend))
    return self


@set_hyperopt_parameters
class MyStrategyNew7(IStrategy):
    # ROI table:
    minimal_roi = {"0": 1}

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.05
    trailing_stop_positive_offset = 0.1
    trailing_only_offset_is_reached = False

    # Stoploss
    stoploss = -1

    # Timeframe
    timeframe = BASE_TIMEFRAME

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        print("Self:", self.__dict__)

    def get_hyperopt_parameters(self, trend: str, condition_idx: int):
        k_1, k_2, k_3, k_4, k_5 = get_parameter_keys(trend, condition_idx)
        indicator = getattr(self, k_1).value
        timeframe = getattr(self, k_2).value
        fperiod = getattr(self, k_3).value
        speriod = getattr(self, k_4).value
        operator = getattr(self, k_5).value
        return indicator, timeframe, fperiod, speriod, operator

    def get_indicators_pair(self, trend: str, condition_idx: int) -> tuple[str, str, str]:
        indicator, timeframe, fperiod, speriod, operator = self.get_hyperopt_parameters(trend, condition_idx)
        first_indicator = f'{indicator}_{PERIODS[fperiod]}_{TIMEFRAMES[timeframe]}'
        second_indicator = f'{indicator}_{PERIODS[speriod]}_{TIMEFRAMES[timeframe]}'
        return first_indicator, second_indicator, operator

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        assert self.dp, "DataProvider is required for multiple timeframes."

        avalidable_indicators = set()
        avalidable_info_timeframes = set()
        avalidable_periods = set()

        run_mode = self.dp.runmode.value
        if run_mode in ('backtest', 'live', 'dry_run'):
            # for these mode only add for current parameters setting
            for trend in ['buy', 'sell']:
                max_conditions = [SELL_MAX_CONDITIONS, BUY_MAX_CONDITIONS][trend == 'buy']
                for condition_idx in range(max_conditions):
                    indicator, timeframe, fperiod, speriod, _ = self.get_hyperopt_parameters(trend, condition_idx)
                    avalidable_indicators.add(indicator)
                    avalidable_info_timeframes.add(TIMEFRAMES[timeframe])
                    avalidable_periods.add(PERIODS[fperiod])
                    avalidable_periods.add(PERIODS[speriod])
        else:
            avalidable_indicators = INDICATORS
            avalidable_info_timeframes = INFO_TIMEFRAMES
            avalidable_periods = PERIODS

        # apply info timeframe indicator
        for info_timeframe in avalidable_info_timeframes:
            info_dataframe = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=info_timeframe)
            for indicator in avalidable_indicators:
                for period in avalidable_periods:
                    apply_indicator(info_dataframe, f'{indicator}_{period}', indicator, period)
            dataframe = merge_informative_pair(dataframe, info_dataframe, self.timeframe, info_timeframe, ffill=True)

        # apply base timeframe indicator
        for indicator in avalidable_indicators:
            for period in avalidable_periods:
                apply_indicator(dataframe, f'{indicator}_{period}_{BASE_TIMEFRAME}', indicator, period)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend = 'buy'

        conditions = list()

        for condition_idx in range(BUY_MAX_CONDITIONS):
            first_indicator, second_indicator, operator = self.get_indicators_pair(trend, condition_idx)
            condition, dataframe = apply_operator(dataframe, first_indicator, second_indicator, operator)
            conditions.append(condition)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend = 'sell'

        conditions = list()

        for condition_idx in range(SELL_MAX_CONDITIONS):
            first_indicator, second_indicator, operator = self.get_indicators_pair(trend, condition_idx)
            condition, dataframe = apply_operator(dataframe, first_indicator, second_indicator, operator)
            conditions.append(condition)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), 'sell'] = 1

        return dataframe
