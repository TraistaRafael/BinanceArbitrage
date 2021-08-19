# BinanceArbitrage

This tool connects to Binance api, checks for arbitrage opportunities realtime and simulates transactions.
An arbitrage oportunity is detected as a profit in exchanging triangle touple of symbols. Example: #  ETH/USD -> USD/BNB -> BNB/ETH

!!!
If you want to perform real transactions based on the opportunities detected by this script please be aware of risks!
!!!

Pull requests are welcome!


# Getting started

Requirements: py 3.x
```
pip install ccxt
py main.py
```

# Arbitrage opportunity hypothetical profitable example
![TriangleArbExample](https://user-images.githubusercontent.com/16855615/130138725-ab2091ef-ce14-421f-8845-92d989165989.png)

