import yfinance as yf
import json
import os

# -----------------------------------------------------------
# Create a python class for a ticker
# -----------------------------------------------------------
class Ticker:
    """
    A class to represent a stock ticker
    """
    def __init__(self, symbol):
        self.symbol = symbol
        self.historical_data = None

    def get_historical_data(self, start_date, end_date, interval='5m', timezone='America/New_York'):
        """
        Get historical data for a given stock ticker
        :param start_date: Start date for historical data (YYYY-MM-DD)
        :param end_date: End date for historical data (YYYY-MM-DD)
        :param interval: Interval for historical data (default: 5m)
        :param timezone: Timezone for historical data (default: America/New_York)
        :return: Historical data for the given stock ticker
        """
        stock_data = yf.download(self.symbol, start=start_date, end=end_date, interval=interval)

        # Convert from UTC to Eastern Time (if data is already tz-aware)
        if stock_data.index.tzinfo is not None:
            stock_data.index = stock_data.index.tz_convert(timezone)
        else:
            # If for any reason data is tz-naive, localize to UTC and then convert
            stock_data.index = stock_data.index.tz_localize('UTC').tz_convert(timezone)

        # summarize the stock information using pandas function
        #print(stock_data.head())
        #print(stock_data.index)
        #print(stock_data.describe())

        self.historical_data = stock_data
        return self.historical_data
    
    def is_valid_symbol(symbol):
        """
        Check if the symbol is a valid symbol
        :return: True if the symbol is valid, False if the symbol is invalid
        """
        try:
            info = yf.Ticker(symbol).info
            if len(info) > 1:
                return True
            return False
        except:
            return False

# -----------------------------------------------------------
# Simulation ticker
# -----------------------------------------------------------
class SimTicker(Ticker):
    """
    A class to represent a simulation ticker
    """
    def __init__(self, symbol):
        super().__init__(symbol)

    def assign_historical_data(self, historical_data):
        """
        Assign historical data to the ticker
        :param historical_data: Historical data for the ticker
        """

        # Create a DataFrame from the historical data
        self.historical_data = historical_data

        return None
    
# -----------------------------------------------------------
# Create a Ticker Manager that manages all Tickers
# -----------------------------------------------------------
class TickerManager:
    """
    A class to represent a ticker manager
    """
    def __init__(self):
        all_data = self.__read_all_tickers()
        self.ticker_list = all_data.get('ticker_list', [])
        self.ticker_obj_list = {}

        # Instantiate the ticker from ticker list
        for ticker in self.ticker_list:
            self.ticker_obj_list[ticker] = Ticker(ticker)

    def __read_all_tickers(self):
        """
        Read the tickers data from the tickers file (tickers.json) present under the .data folder
        """
        # Read the tickers data from the tickers file which is a JSON file and store the data as a dictionary
        # If the folder or file is not present, create a empty dictionary and a empty file
        all_data = {}
        file_name = '1_ticker_manager.json'
        try:
            # check for the folder present and if not present create the folder
            if not os.path.exists('.data'):
                os.makedirs('.data')

            with open(f'.data/{file_name}', 'r') as tickers_file:
                tickers_data = tickers_file.read()
                all_data = json.loads(tickers_data)
        except FileNotFoundError:
            with open(f'.data/{file_name}', 'w') as tickers_file:
                tickers_file.write(json.dumps(all_data))
        except json.decoder.JSONDecodeError:
            all_data = {}
        return all_data

    def __write_all_tickers(self, data):
        """
        Write the tickers data to the tickers file (tickers.json) present under the .data folder
        """
        file_name = '1_ticker_manager.json'
        # Write the tickers data to the tickers file which is a JSON file
        with open(f'.data/{file_name}', 'w') as tickers_file:
            tickers_file.write(json.dumps(data))

    def add_ticker(self, symbol):
        """
        Add a ticker to the ticker manager
        :param symbol: Symbol for the ticker
        :param ticker: Ticker object
        :return: True if the ticker is added, False if the ticker is already in the ticker list
        """
        # Check if the ticker is already in the ticker list
        if symbol not in self.ticker_list:
            self.ticker_list.append(symbol)
            self.ticker_obj_list[symbol] = Ticker(symbol)
            return {
                "status": True,
                "message": f"Ticker {symbol} added successfully"
            }
        return {
            "status": False,
            "message": f"Ticker {symbol} already present"
        }
    
    def remove_ticker(self, symbol):
        """
        Remove a ticker from the ticker manager
        :param symbol: Symbol for the ticker
        :return: True if the ticker is removed, False if the ticker is not in the ticker list
        """
        # Check if the ticker is already in the ticker list
        if symbol in self.ticker_list:
            self.ticker_list.remove(symbol)
            del self.ticker_obj_list[symbol]
            return True
        return False

    def lazy_add_ticker(self, symbol):
        """
        Adds the ticker to the ticker manager file if not already present
        :param symbol: Symbol for the ticker
        """
        if symbol not in self.ticker_list:
            # Check if the symbol is valid
            if Ticker.is_valid_symbol(symbol):
                all_data = self.__read_all_tickers()
                all_data['ticker_list'] = self.ticker_list + [symbol]
                self.__write_all_tickers(all_data)
                return  { "status": True, "message": f"Ticker {symbol} added successfully"}
            else:
                return { "status": False, "message": f"Ticker {symbol} is not a valid symbol"}
        return { "status": False, "message": f"Ticker {symbol} already present in the existing list"}

    def lazy_remove_ticker(self, symbol):
        """
        Removes the ticker from the ticker manager file if present
        :param symbol: Symbol for the ticker
        """
        if symbol in self.ticker_list:
            all_data = self.__read_all_tickers()
            all_data['ticker_list'] = [ticker for ticker in self.ticker_list if ticker != symbol]
            self.__write_all_tickers(all_data)
            return { "status": True, "message": f"Ticker {symbol} removed successfully"}
        return { "status": False, "message": f"Ticker {symbol} not present in the existing list"}

    def sync_tickers(self):
        """
        Read the tickers data from the tickers file (tickers.json) present under the .data folder
        If there are any new symbol or removed symbol, update the ticker list and the ticker object list
        """ 
        all_data = self.__read_all_tickers()
        new_ticker_list = all_data.get('ticker_list', [])
        for symbol in new_ticker_list:
            if symbol not in self.ticker_list:
                self.ticker_list.append(symbol)
                self.ticker_obj_list[symbol] = Ticker(symbol)
        for symbol in self.ticker_list:
            if symbol not in new_ticker_list:
                self.ticker_list.remove(symbol)
                del self.ticker_obj_list[symbol]

    def get_ticker(self, symbol):
        """
        Get a ticker from the ticker manager
        :param symbol: Symbol for the ticker
        :return: Ticker object
        """
        return self.ticker_obj_list.get(symbol, None)

    def get_all_tickers(self):
        """
        Get all tickers from the ticker manager
        :return: Ticker objects
        """
        return self.ticker_obj_list
    