"""
This tool connects to Binance api, checks for arbitrage opportunities realtime and simulates transactions.
An arbitrage oportunity is detected as a profit in exchanging triangle touple of symbols. Example: #  ETH/USD -> USD/BNB -> BNB/ETH

!!!
If you want to perform real transactions based on the opportunities detected by this script please be aware of risks!
!!!

Pull requests are welcome!


MIT License

Copyright (c) 2021 TraistaRafael

traista.rafael@yahoo.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OT5HER DEALINGS IN THE
SOFTWARE.
"""

import ccxt
import time

# Update this value according to Binance policy
EXCHANGE_FEE = 0.001 

# EG: for the touple: BNB/ETH -> ETH/USD -> USD/BNB then for TRADE_INVEST_UNITS = 1, 1 Bitcoin will be traded via this 3 pairs.
# How many units of the first touple currency are traded on each oportunity.
TRADE_INVEST_UNITS = 1 

# Look only for touples wich include at least one of the currencies listed below. 
FILTER_SYMBOL_LISTS = ["ETH", "BTC", "EGLD", "DOT", "BTT", "BNB", "IOTA", "LTC", "DOGE"] 

class TriangleArbitrage():

    def __init__(self):
        self._all_pairs = []
        self._triangle_touples = []
        self._twm = None
        self._tickers = None
        self.exchange_api = ccxt.binance()
    

    def run(self):
        """
        Main looping function. Each 2 seconds, fetch all tickers from binance API and check for oportunity

        Parameters
        ----------
        symbol : string
            trading symbol, eg: ETH/BTC
        """
        while True:
            self._tickers = self.exchange_api.fetch_tickers()

            # If this is the first tick, register all trading pairs as member for quicker access
            if len(self._all_pairs) == 0:
                self._all_pairs = self.get_all_pairs()

            # If this is the first tick, find all possible valid arbitrage touples of 3 symbols. EG:
            #  ETH/USD -> USD/BNB -> BNB/ETH
            if len(self._triangle_touples) == 0:
                all_triangle_pairs = self.get_triangle_pairs()
                self._triangle_touples = self.filter_valid_triangle_pairs(all_triangle_pairs)
            
            self.check_for_oportunity()

            time.sleep(2)


    def get_ticker_by_symbol(self, symbol):
        """
        Get the binance ticker for some trading symbol

        Parameters
        ----------
        symbol : string
            trading symbol, eg: ETH/BTC
        """

        if self._tickers is None:
            print ("missing self._last_ticker_data {}".format(symbol))
            return None
        if symbol in self._tickers:
            return self._tickers[symbol]
        else:
            return None
       

    def symbol_is_valid(self, symbol):
        if symbol not in self._all_pairs:
            return False
        if self.get_ticker_by_symbol(symbol) is None:
            return False
        else:
            return True


    def get_symbol_ask(self, symbol):
        element = self.get_ticker_by_symbol(symbol)
        if element is None:
            return -1
        else:
            return float(element["ask"])


    def get_symbol_bid(self, symbol):
        element = self.get_ticker_by_symbol(symbol)
        if element is None:
            return -1
        else:
            return float(element['bid'])

    
    def get_left_symbol(self, pair):
        splitted = pair.split("/")
        return splitted[0]


    def get_right_symbol(self, pair):
        splitted = pair.split("/")
        return splitted[1]


    def get_all_pairs(self):
        all_pairs = []

        for symbol in self._tickers:
            if float(self._tickers[symbol]['ask']) > 0 and float(self._tickers[symbol]['bid']) > 0:
                all_pairs.append(symbol)
            else:
                continue

        return all_pairs


    def index_pairs_by_symbol_position(self):
        """
        This will index all pairs into a dictionary wich will be later used to generate the final valid arbitrage touples.

        Return
        --------
        dictionary
            For each currency symbol, the dictionary will have the trading pairs where this currency is to the right, to the left and both.
            EG: 'ETH': {
                'left': ['ETH/BNB', 'ETH/USD']
                'right': ['USDT/ETH']
                'all': ['ETH/BNB', 'ETH/USD, 'USDT/ETH']
            }
        """
        indexed_pairs = {}

        for pair in self._all_pairs:
            left_symbol = self.get_left_symbol(pair)
            right_symbol = self.get_right_symbol(pair)

            if left_symbol not in indexed_pairs:
                indexed_pairs[left_symbol] = {"left": [], "right": [], "all": []}
            
            if right_symbol not in indexed_pairs:
                indexed_pairs[right_symbol] = {"left": [], "right": [], "all": []}

            indexed_pairs[left_symbol]["left"].append(pair)
            indexed_pairs[right_symbol]["right"].append(pair)

            indexed_pairs[left_symbol]["all"].append(pair)
            indexed_pairs[right_symbol]["all"].append(pair)

        return indexed_pairs


    def get_triangle_pairs(self):
        """
        Find valid touples of 3 symbols wich can be transactioned in loop.
        Filter only pairs wich have at least one of the FILTER_SYMBOLS_LIST
        """
        all_pairs = self.get_all_pairs()
        indexed_pairs = self.index_pairs_by_symbol_position()
        filter_symbols = FILTER_SYMBOL_LISTS
        triangles = []

        for start_symbol in filter_symbols:
            if start_symbol not in indexed_pairs:
                continue

            left_pairs = indexed_pairs[start_symbol]["all"]
            right_pairs = indexed_pairs[start_symbol]["all"]

            for left_pair in left_pairs:
                for right_pair in right_pairs:
                    if left_pair == right_pair:
                        continue

                    left_symbol_a = self.get_left_symbol(left_pair)
                    left_symbol_b = self.get_right_symbol(left_pair)
                    right_symbol_a = self.get_left_symbol(right_pair)
                    right_symbol_b = self.get_right_symbol(right_pair)

                    if left_symbol_a == right_symbol_a:
                        mid_pair = left_symbol_b + "/" + right_symbol_b
                        if mid_pair in all_pairs:
                            triangles.append((left_pair, mid_pair, right_pair))
                    elif left_symbol_a == right_symbol_b:
                        mid_pair = left_symbol_b + "/" + right_symbol_a
                        if mid_pair in all_pairs:
                            triangles.append((left_pair, mid_pair, right_pair))


        return triangles


    def filter_valid_triangle_pairs(self, triangle_pairs):
        """
        Some trading symbols provided by the binance API are not valid, we will filter only valid prices

        Parameters
        ------------
        triangle_pairs: list
        """
        valid_touples = []

        print ("pairs to validate: {}".format(len(triangle_pairs)))

        for triangle_touple in triangle_pairs:
            left_pair = triangle_touple[0]
            mid_pair = triangle_touple[1]
            right_pair = triangle_touple[2]

            left_ask = self.get_symbol_ask(left_pair)
            left_bid = self.get_symbol_bid(left_pair)
            mid_ask = self.get_symbol_ask(mid_pair)
            mid_bid = self.get_symbol_bid(mid_pair)
            right_ask = self.get_symbol_ask(right_pair)
            right_bid = self.get_symbol_bid(right_pair)

            if left_bid <= 0 or left_ask <= 0 or mid_bid <= 0 or mid_ask <= 0 or right_bid <= 0 or right_ask <= 0: 
                continue

            valid_touples.append(triangle_touple)
        
        return valid_touples


    def check_for_oportunity(self):
        print("Checking for aribitrage oportunity.")
        triangles_processed = 0
        best_profit = -1

        for triangle_touple in self._triangle_touples:
            left_pair = triangle_touple[0]
            mid_pair = triangle_touple[1]

            max_diff = 0
            profit = 0
           
            # Get the three currencies involved in this arbitrage oportunity
            A = self.get_left_symbol(left_pair)
            B = self.get_right_symbol(left_pair)
            C = self.get_left_symbol(mid_pair)
            if B == C:
                C = self.get_right_symbol(mid_pair)

            # Init trading ratios between this 3 prices
            AB = 1
            BC = 1
            CA = 1
            
            # Update trading ratios with real values
            if self.symbol_is_valid(A + "/" + B):
                AB = self.get_symbol_bid(A + "/" + B)
            elif self.symbol_is_valid(B + "/" + A):
                AB = 1 / self.get_symbol_ask(B + "/" + A)
            else:
                break

            if self.symbol_is_valid(B + "/" + C):
                BC = self.get_symbol_bid(B + "/" + C)
            elif self.symbol_is_valid(C + "/" + B):
                BC = 1 / self.get_symbol_ask(C + "/" + B)
            else:
                break

            if self.symbol_is_valid(C + "/" + A):
                CA = self.get_symbol_bid(C + "/" + A)
            elif self.symbol_is_valid(A + "/" + C):
                CA = 1 / self.get_symbol_ask(A + "/" + C)
            else:
                break 
            
            # Apply binance's transaction fee in order to make the simulation more realistic.
            AB -= EXCHANGE_FEE * AB
            BC -= EXCHANGE_FEE * BC
            CA -= EXCHANGE_FEE * CA

            # Compute arbitrage profit
            arb_CA = 1 / (AB * BC)

            arb_diff = abs(CA - arb_CA)

            # perform investment calculations
            initial_A = TRADE_INVEST_UNITS
            convert_to_B = initial_A * AB
            convert_to_C = convert_to_B * BC
            final_A = convert_to_C * CA

            instant_profit = final_A - initial_A
            if instant_profit > best_profit:
                best_profit = instant_profit

            # If this is a profitable transaction, print details
            if final_A > initial_A:
                print ("Valid transaction details: {}   AB: {:.5f}   BC: {:.5f}   CA:  {:.5f}   1x{} -> {:.5} x {} -> {:.5f} x {} -> {:.5f} x {}".format(
                    triangle_touple,
                    AB, BC, CA,
                    A,
                    convert_to_B, B,
                    convert_to_C, C,
                    final_A, A
                ))
                
            triangles_processed += 1

        print ("Triangles processed: {}  best profit: {:.5f}".format(triangles_processed, best_profit))



# Init execution
if __name__ == "__main__":
    arbitrag_instance = TriangleArbitrage()
    arbitrag_instance.run()