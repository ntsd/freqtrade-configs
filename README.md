# My Freqtrade strategies and config

## Configs

### Using minimal roi

key mean hours time

value mean percentage of profit

example: "12": 0.064 mean after 12 hours holding if the profit positive more than 6.4% will automatic sell

but for testing no minimal_roi is probably the best

```json
"minimal_roi": {
    "0": 0.177,
    "12": 0.064,
    "63": 0.023,
    "110": 0
},
```

### Trailing stop

```json
"trailing_stop": true,
"trailing_stop_positive": 0.079,
"trailing_stop_positive_offset": 0.156,
"trailing_only_offset_is_reached": true
```
