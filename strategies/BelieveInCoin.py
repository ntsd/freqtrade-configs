# BelieveInCoin
# This strategy is for people who believe in a coin. Best for 1 pair and 1 max open trade.
# Author: @ntsd (Jirawat Boonkumnerd)
# Github: https://github.com/ntsd
# freqtrade download-data --exchange binanceusdm -t 5m 15m 1h 4h --days 500
# freqtrade download-data --exchange binanceusdm -t 1d --days 1000
# ProfitDrawDownHyperOptLoss, ShortTradeDurHyperOptLoss, OnlyProfitHyperOptLoss, SharpeHyperOptLoss, SharpeHyperOptLossDaily, SortinoHyperOptLoss, SortinoHyperOptLossDaily
# freqtrade hyperopt --hyperopt-loss OnlyProfitHyperOptLoss --spaces buy sell --timeframe 5m -e 10000 --print-all --strategy BelieveInCoin -j 12
# freqtrade backtesting --timeframe 5m --strategy BelieveInCoin --timerange=20220101-
# freqtrade backtesting --timeframe 5m --strategy-list BelieveInCoin NostalgiaForInfinityX --timerange=20220101-

from freqtrade.strategy import IStrategy, CategoricalParameter, IntParameter, merge_informative_pair
from freqtrade.enums import SignalType
from pandas import DataFrame, Series

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from functools import reduce
import numpy as np

########################### Static Parameters ###########################
IS_HYPEROPT = True
INDICATORS = ("EMA", "SMA")

# Timeframes available for the exchange `Binance`: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
BASE_TIMEFRAME = "5m"

BUY_TIMEFRAMES = ("5m", "15m", "1h", "1d")
BUY_MAX_CONDITIONS = len(BUY_TIMEFRAMES)

SELL_TIMEFRAMES = ("5m", "15m", "1h", "1d")
SELL_MAX_CONDITIONS = len(SELL_TIMEFRAMES)

INFO_TIMEFRAMES = set(BUY_TIMEFRAMES + SELL_TIMEFRAMES) - {"5m"}

BTC_TIMEFRAMES = ("1h", "1d")

PERIODS = []
n = 5
for i in range(1, 15):
    PERIODS.append(n)
    n += i
PERIODS_LEN = len(PERIODS)


########################### Default hyperopt parameter ###########################
# Buy hyperspace params:
buy_params = {
    "buy_fperiod_0": 6,
    "buy_fperiod_1": 11,
    "buy_fperiod_2": 9,
    "buy_fperiod_3": 10,
    "buy_indicator_0": "EMA",
    "buy_indicator_1": "EMA",
    "buy_indicator_2": "SMA",
    "buy_indicator_3": "SMA",
    "buy_speriod_0": 9,
    "buy_speriod_1": 10,
    "buy_speriod_2": 12,
    "buy_speriod_3": 13,
}

# Sell hyperspace params:
sell_params = {
    "sell_fperiod_0": 9,
    "sell_fperiod_1": 1,
    "sell_fperiod_2": 3,
    "sell_fperiod_3": 7,
    "sell_indicator_0": "EMA",
    "sell_indicator_1": "EMA",
    "sell_indicator_2": "SMA",
    "sell_indicator_3": "EMA",
    "sell_speriod_0": 13,
    "sell_speriod_1": 13,
    "sell_speriod_2": 5,
    "sell_speriod_3": 1,
}

########################### Indicator ###########################
def normalize(df):
    df = (df - df.min()) / (df.max() - df.min())
    return df


def apply_indicator(dataframe: DataFrame, key: str, indicator: str, period: int):
    if key in dataframe.keys():
        return

    result = getattr(ta, indicator)(dataframe, timeperiod=period)
    # dataframe[key] = normalize(result)
    dataframe[key] = result


########################### Operators ###########################
def greater_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return dataframe[main_indicator] > dataframe[crossed_indicator]


def lower_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return dataframe[main_indicator] < dataframe[crossed_indicator]


def true_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return dataframe["volume"] > 10


def close_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return np.isclose(dataframe[main_indicator], dataframe[crossed_indicator])


def crossed_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return (qtpylib.crossed_below(dataframe[main_indicator], dataframe[crossed_indicator])) | (
        qtpylib.crossed_above(dataframe[main_indicator], dataframe[crossed_indicator])
    )


def crossed_above_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return qtpylib.crossed_above(dataframe[main_indicator], dataframe[crossed_indicator])


def crossed_below_operator(dataframe: DataFrame, main_indicator: str, crossed_indicator: str):
    return qtpylib.crossed_below(dataframe[main_indicator], dataframe[crossed_indicator])


OPERATORS = {
    "D": true_operator,
    ">": greater_operator,
    "<": lower_operator,
    "=": close_operator,
    "C": crossed_operator,
    "CA": crossed_above_operator,
    "CB": crossed_below_operator,
}


def apply_operator(dataframe: DataFrame, main_indicator, crossed_indicator, operator) -> tuple[Series, DataFrame]:
    condition = OPERATORS[operator](dataframe, main_indicator, crossed_indicator)
    return condition, dataframe


########################### HyperOpt Parameters ###########################


class DefaultValue:
    def __init__(self, value) -> None:
        self.value = value


def get_hyperopt_parameter_keys(trend: str, condition_idx: int):
    k_1 = f"{trend}_indicator_{condition_idx}"
    k_2 = f"{trend}_fperiod_{condition_idx}"
    k_3 = f"{trend}_speriod_{condition_idx}"
    return k_1, k_2, k_3


def set_hyperopt_parameters(self):
    trend = "buy"
    for condition_idx in range(BUY_MAX_CONDITIONS):
        k_1, k_2, k_3 = get_hyperopt_parameter_keys(trend, condition_idx)
        if IS_HYPEROPT:
            setattr(self, k_1, CategoricalParameter(INDICATORS, space=trend, default=buy_params[k_1]))
            setattr(self, k_2, IntParameter(0, PERIODS_LEN - 1, space=trend, default=buy_params[k_2]))
            setattr(self, k_3, IntParameter(0, PERIODS_LEN - 1, space=trend, default=buy_params[k_3]))
        else:
            setattr(self, k_1, DefaultValue(buy_params[k_1]))
            setattr(self, k_2, DefaultValue(buy_params[k_2]))
            setattr(self, k_3, DefaultValue(buy_params[k_3]))

    trend = "sell"
    for condition_idx in range(SELL_MAX_CONDITIONS):
        k_1, k_2, k_3 = get_hyperopt_parameter_keys(trend, condition_idx)
        if IS_HYPEROPT:
            setattr(self, k_1, CategoricalParameter(INDICATORS, space=trend, default=sell_params[k_1]))
            setattr(self, k_2, IntParameter(0, PERIODS_LEN - 1, space=trend, default=sell_params[k_2]))
            setattr(self, k_3, IntParameter(0, PERIODS_LEN - 1, space=trend, default=sell_params[k_3]))
        else:
            setattr(self, k_1, DefaultValue(sell_params[k_1]))
            setattr(self, k_2, DefaultValue(sell_params[k_2]))
            setattr(self, k_3, DefaultValue(sell_params[k_3]))

    return self


########################### Strategy ###########################
@set_hyperopt_parameters
class BelieveInCoin(IStrategy):
    def leverage(self, pair: str, current_time, current_rate: float, proposed_leverage: float, max_leverage: float, side: str, **kwargs) -> float:
        return 5.0

    INTERFACE_VERSION = 3

    # ROI table:
    minimal_roi = {"0": 100.0}

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = False

    # Stoploss
    stoploss = -0.99

    # Timeframe
    timeframe = BASE_TIMEFRAME

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count = 500

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        print("Self:", self.__dict__)

    ########################### Populate Indicators ###########################
    def drop_timeframe_data(self, dataframe: DataFrame, timeframe: str) -> DataFrame:
        drop_columns = [f"{s}_{timeframe}" for s in ["date", "open", "high", "low", "close", "volume"]]
        dataframe.drop(columns=dataframe.columns.intersection(drop_columns), inplace=True)
        return dataframe

    def info_tf_btc_indicators(self, dataframe: DataFrame) -> DataFrame:
        dataframe["btc_rsi_14"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["btc_not_downtrend"] = (dataframe["close"] > dataframe["close"].shift(2)) | (dataframe["btc_rsi_14"] > 50)

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # BTC informative (1h)
        btc_info_pair = "BTC/USDT"
        for btc_timeframe in BTC_TIMEFRAMES:  # btc_not_downtrend_1h, btc_not_downtrend_1d
            btc_info_tf = self.dp.get_pair_dataframe(btc_info_pair, btc_timeframe)
            btc_info_tf = self.info_tf_btc_indicators(btc_info_tf)
            dataframe = merge_informative_pair(dataframe, btc_info_tf, self.timeframe, btc_timeframe, ffill=True)
            dataframe = self.drop_timeframe_data(dataframe, btc_timeframe)

        # Get available parameters
        available_indicators = set()
        available_info_timeframes = set()
        available_periods = set()

        run_mode = self.dp.runmode.value
        if run_mode in ("backtest", "live", "dry_run"):  # for these run mode shoud add only available parameters
            for condition_idx in range(BUY_MAX_CONDITIONS):
                indicator, fperiod, speriod = self.get_hyperopt_parameters("buy", condition_idx)
                available_indicators.add(indicator)
                available_info_timeframes.add(BUY_TIMEFRAMES[condition_idx])
                available_periods.add(PERIODS[fperiod])
                available_periods.add(PERIODS[speriod])
            for condition_idx in range(SELL_MAX_CONDITIONS):
                indicator, fperiod, speriod = self.get_hyperopt_parameters("sell", condition_idx)
                available_indicators.add(indicator)
                available_info_timeframes.add(SELL_TIMEFRAMES[condition_idx])
                available_periods.add(PERIODS[fperiod])
                available_periods.add(PERIODS[speriod])
        else:
            available_indicators = INDICATORS
            available_info_timeframes = INFO_TIMEFRAMES
            available_periods = PERIODS

        # apply info timeframe indicator
        for info_timeframe in available_info_timeframes:
            info_dataframe = self.dp.get_pair_dataframe(pair=metadata["pair"], timeframe=info_timeframe, candle_type="futures")
            for indicator in available_indicators:
                for period in available_periods:
                    apply_indicator(info_dataframe, f"{indicator}_{period}", indicator, period)
            dataframe = merge_informative_pair(dataframe, info_dataframe, self.timeframe, info_timeframe, ffill=True)

        # apply base timeframe indicator
        for indicator in available_indicators:
            for period in available_periods:
                apply_indicator(dataframe, f"{indicator}_{period}_{BASE_TIMEFRAME}", indicator, period)

        # print(list(dataframe.keys()))

        return dataframe

    ########################### Strategy Logic ###########################
    def get_hyperopt_parameters(self, trend: str, condition_idx: int):
        k_1, k_2, k_3 = get_hyperopt_parameter_keys(trend, condition_idx)
        indicator = getattr(self, k_1).value
        fperiod = getattr(self, k_2).value
        speriod = getattr(self, k_3).value
        return indicator, fperiod, speriod

    def get_indicators_pair(self, trend: str, condition_idx: int) -> tuple[str, str, str]:
        indicator, fperiod, speriod = self.get_hyperopt_parameters(trend, condition_idx)

        if fperiod == speriod:
            return None, None, None

        if trend == "sell":
            operator = "CB" if condition_idx == 0 else "<"
            main_indicator = f"{indicator}_{PERIODS[fperiod]}_{SELL_TIMEFRAMES[condition_idx]}"
            crossed_indicator = f"{indicator}_{PERIODS[speriod]}_{SELL_TIMEFRAMES[condition_idx]}"
        else:
            operator = "CA" if condition_idx == 0 else ">"
            main_indicator = f"{indicator}_{PERIODS[fperiod]}_{BUY_TIMEFRAMES[condition_idx]}"
            crossed_indicator = f"{indicator}_{PERIODS[speriod]}_{BUY_TIMEFRAMES[condition_idx]}"

        return main_indicator, crossed_indicator, operator

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend = "buy"
        conditions = list()

        # BTC Condition TODO: Add crsi_1h
        for btc_timframe in BTC_TIMEFRAMES:
            conditions.append(dataframe[f"btc_not_downtrend_{btc_timframe}"] == True)

        for condition_idx in range(BUY_MAX_CONDITIONS):
            main_indicator, crossed_indicator, operator = self.get_indicators_pair(trend, condition_idx)
            if not operator:
                continue
            condition, dataframe = apply_operator(dataframe, main_indicator, crossed_indicator, operator)
            conditions.append(condition)

        if conditions:
            dataframe.loc[:, SignalType.ENTER_LONG.value] = reduce(lambda x, y: x & y, conditions)

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend = "sell"
        conditions = list()

        # BTC Condition TODO: Add crsi_1h
        for btc_timframe in BTC_TIMEFRAMES:
            conditions.append(dataframe[f"btc_not_downtrend_{btc_timframe}"] == False)

        for condition_idx in range(BUY_MAX_CONDITIONS):
            main_indicator, crossed_indicator, operator = self.get_indicators_pair(trend, condition_idx)
            if not operator:
                continue
            if operator:
                condition, dataframe = apply_operator(dataframe, main_indicator, crossed_indicator, operator)
                conditions.append(condition)

        if conditions:
            dataframe.loc[:, SignalType.EXIT_LONG.value] = reduce(lambda x, y: x & y, conditions)

        return dataframe
