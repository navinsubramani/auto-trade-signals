import datetime
import asyncio
import time

from module.trade.ticker import TickerManager
from module.trade.indicator.signal_satypivotribbon import SignalSatypePivotRibbon

from module.trade.ticker import Ticker

class GenerateIndicator:
    def __init__(self, data_range_days=10, data_interval_minutes=5):
        """
        Initialize the generate indicator flow
        :param data_range_days: Number of days to get the historical data
        :param data_interval_minutes: Interval in minutes for the historical data
        """
        self.Ticker_Manager = TickerManager()
        self.Signal_List = [
            SignalSatypePivotRibbon()
        ]
        self.data_range_days = data_range_days
        self.data_interval_minutes = data_interval_minutes

    async def execute_gi_single_ticker(self, ticker_obj, publish_signal_func=None):
        """
        Execute the generate indicator flow for a single ticker
        """
        # Get the start and end date for the historical data
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=self.data_range_days)).strftime('%Y-%m-%d')
        end_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        interval = f"{self.data_interval_minutes}m"

        ticker = ticker_obj.symbol

        try:
            print(f"Getting historical data for {ticker}")

            ticker_obj.get_historical_data(
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                timezone='America/New_York'
                )

            # Execute the signals for the ticker
            for signal in self.Signal_List:
                print(f"Executing signal: {signal.signal_name} for {ticker}")
                result = signal.compute(ticker_obj)
                if result['signal']:
                    print(result)
                    plot = signal.compute_and_plot(ticker_obj)
                    plot = plot["buf"]
                    if publish_signal_func is not None:
                        await publish_signal_func(result, buf=plot)
        except Exception as e:
            print(f"Error getting historical data, executing the signal or publishing results for {ticker}: {e}")

    async def execute_gi(self, publish_signal_func=None):
        """
        Execute the generate indicator flow
        """
        self.Ticker_Manager.sync_tickers()
        # for each ticker in the ticker manager, get the historical data
        print("Executing signals: All Started")

        # Get the historical data for each ticker
        for ticker in self.Ticker_Manager.get_all_tickers():
            ticker_obj = self.Ticker_Manager.get_all_tickers()[ticker]
            await self.execute_gi_single_ticker(ticker_obj, publish_signal_func)

        print("Executing signals: All Completed")
    
    async def excute_gi_ondemand(self, symbol, publish_signal_func=None):
        """
        Execute the generate indicator flow for a single ticker
        """
        if Ticker.is_valid_symbol(symbol) is False:
            print(f"Invalid symbol: {symbol}")
            await publish_signal_func({
                "symbol": symbol,
                "name": "Invalid Symbol",
                "message": f"The given symbol: {symbol} is invalid or the symbol is delisted recently or the data is not available in Yahoo Finance. Please provide a valid symbol.",
                "signal": False
            })
        else:
            ticker_obj = Ticker(symbol=symbol)
            today = datetime.date.today()
            start_date = (today - datetime.timedelta(days=self.data_range_days)).strftime('%Y-%m-%d')
            end_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            interval = f"{self.data_interval_minutes}m"

            ticker = ticker_obj.symbol

            try:
                print(f"Getting historical data for {ticker}")

                ticker_obj.get_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    timezone='America/New_York'
                    )

                # Execute the signals for the ticker
                for signal in self.Signal_List:
                    print(f"Executing signal: {signal.signal_name} for {ticker}")
                    result = {
                        "symbol": ticker,
                        "name": signal.signal_name,
                        "message": "",
                        "signal": False
                    }
                    print(result)
                    plot = signal.compute_and_plot(ticker_obj)
                    plot = plot["buf"]
                    if publish_signal_func is not None:
                        await publish_signal_func(result, buf=plot)
            except Exception as e:
                print(f"Error getting historical data, executing the signal or publishing results for {ticker}: {e}")

    def add_symbol(self, symbol):
        """
        Add a symbol to the ticker manager
        :param symbol: Symbol to add
        """
        return self.Ticker_Manager.lazy_add_ticker(symbol)
    
    def remove_symbol(self, symbol):
        """
        Remove a symbol from the ticker manager
        :param symbol: Symbol to remove
        """
        return self.Ticker_Manager.lazy_remove_ticker(symbol)
    
    def get_all_symbols(self):
        """
        Get all the symbols in the ticker manager
        """
        return self.Ticker_Manager.get_all_tickers().keys()

if __name__ == "__main__":
    gi = GenerateIndicator()
    gi.execute_gi()