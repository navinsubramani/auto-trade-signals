import datetime
import asyncio
import time

from module.trade.ticker import TickerManager
from module.trade.indicator.signal_satypivotribbon import SignalSatypePivotRibbon

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

    async def execute_gi(self, publish_signal_func=None):
        """
        Execute the generate indicator flow
        """
        self.Ticker_Manager.sync_tickers()
        # for each ticker in the ticker manager, get the historical data
        print("Executing signals: All Started")

        # Get the start and end date for the historical data
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=self.data_range_days)).strftime('%Y-%m-%d')
        end_date = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        interval = f"{self.data_interval_minutes}m"

        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")
        print(f"Interval: {interval}")

        # Get the historical data for each ticker
        for ticker in self.Ticker_Manager.get_all_tickers():
            try:
                print(f"Getting historical data for {ticker}")
                obj = self.Ticker_Manager.get_all_tickers()[ticker]
                obj.get_historical_data(
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    timezone='America/New_York'
                    )

                # Execute the signals for the ticker
                for signal in self.Signal_List:
                    print(f"Executing signal: {signal.signal_name} for {ticker}")
                    obj = self.Ticker_Manager.get_all_tickers()[ticker]
                    result = signal.compute(obj)
                    if result['signal']:
                        print(result)
                        plot = signal.compute_and_plot(obj)
                        plot = plot["buf"]
                        if publish_signal_func is not None:
                            await publish_signal_func(result, buf=plot)
            except Exception as e:
                print(f"Error getting historical data, executing the signal or publishing results for {ticker}: {e}")
                continue

        print("Executing signals: All Completed")
    
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