# My Freqtrade strategies and config

## How to optimise parameter

```bash
# install python3.9-dev and pip if not avaliable
sudo apt install python3.9-dev
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.9 get-pip.py

# clone repo
git clone -b develop https://github.com/freqtrade/freqtrade.git
cd freqtrade

# setup and activate env
./setup.sh --install
source .env/bin/activate

# create profile
freqtrade new-config --config user_data/config.json

# change config pairs manual
# download data
freqtrade download-data --exchange binance -t 5m --days 500

# use hyperopt to optimise strategy parameters by buy and sell signal
# read this for the loss function https://www.freqtrade.io/en/stable/hyperopt/#loss-functions
# ShortTradeDurHyperOptLoss (default legacy Freqtrade hyperoptimization loss function) - Mostly for short trade duration and avoiding losses.
# OnlyProfitHyperOptLoss (which takes only amount of profit into consideration)
# SharpeHyperOptLoss (optimizes Sharpe Ratio calculated on trade returns relative to standard deviation)
# SharpeHyperOptLossDaily (optimizes Sharpe Ratio calculated on daily trade returns relative to standard deviation)
# SortinoHyperOptLoss (optimizes Sortino Ratio calculated on trade returns relative to downside standard deviation)
# SortinoHyperOptLossDaily (optimizes Sortino Ratio calculated on daily trade returns relative to downside standard deviation)
freqtrade hyperopt --hyperopt-loss SharpeHyperOptLoss --spaces buy sell --timerange 20210101-20210807 --timeframe 5m --strategy MyStrategyNew10 --print-all

# update parameters to default config inside strategy python file

# use hyperopt to optimise roi and trailing configs parameters
freqtrade hyperopt --hyperopt-loss OnlyProfitHyperOptLoss --spaces roi trailing --timerange 20210101-20210807 --timeframe 5m --strategy MyStrategyNew10 --print-all

# update minimal_roi and trailing_stop to config

# backtesting
freqtrade backtesting --timeframe 5m --strategy MyStrategyNew10 

# or compare list
freqtrade backtesting --timeframe 5m --timerange 20210301-20210807 --strategy-list MyStrategyNew10 NostalgiaForInfinityV7 

# plot backtest
freqtrade plot-dataframe --strategy MyStrategyNew10  --timerange=20210701-20210813
```

## How to run (docker)

```sh
mkdir ft_userdata
cd ft_userdata/
# Download the docker-compose file from the repository
curl https://raw.githubusercontent.com/freqtrade/freqtrade/stable/docker-compose.yml -o docker-compose.yml

# Pull the freqtrade image
docker-compose pull

# Create user directory structure
docker-compose run --rm freqtrade create-userdir --userdir user_data

# Create configuration - Requires answering interactive questions
docker-compose run --rm freqtrade new-config --config user_data/config.json

# add credential and configs
# add strategies
# edit docker-compose.yml CMD to change strategy

# run via docker-compose
docker-compose up -d
```

## Configs

### Using minimal roi

example: "12": 0.064 mean after 12 mins holding if the profit positive more than 6.4% will automatic sell

but for testing no minimal_roi is probably the best

```json
"minimal_roi": {
    "0": 0.16,
    "21": 0.037,
    "64": 0.012,
    "178": 0
}
```

### Trailing stop

```json
"trailing_stop": true,
"trailing_stop_positive": 0.079,
"trailing_stop_positive_offset": 0.156,
"trailing_only_offset_is_reached": true
```

### Pair list

use `docker-compose run freqtrade test-pairlist` to check the pairlist

ref <https://www.freqtrade.io/en/stable/includes/pairlists/>

example

```json
"exchange": {
    "pair_whitelist": [],
    "pair_blacklist": [
        ".*BEAR/BTC",
        ".*BULL/BTC",
        ".*UP/BTC",
        ".*DOWN/BTC",
        ".*HEDGE/BTC",
    ]
},
"pairlists": [
    {
        "method": "VolumePairList",
        "number_assets": 20,
        "sort_key": "quoteVolume"
    },
    {"method": "AgeFilter", "min_days_listed": 7},
    {
        "method": "RangeStabilityFilter",
        "lookback_days": 10,
        "min_rate_of_change": 0.01,
        "refresh_period": 1440
    },
    {"method": "ShuffleFilter"}
],
```
