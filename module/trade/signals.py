import os
import json

# Create a base class for the signals

class SignalBase:
    """
    A class to represent a signal
    """
    def __init__(self) -> None:
        self.signal_name = "base"
        pass

    def __read_all_cache(self, symbol):
        """
        Read the cache data from the cache file (symbol.cache) present under the .data folder for the ticker
        """
        
        # Read the cache data from the cache file which is a JSON file and store the data as a dictionary
        # If the folder or file is not present, create a empty dictionary and a empty file
        all_data = {}
        try:
            # check for the folder present and if not present create the folder
            if not os.path.exists('.data'):
                os.makedirs('.data')

            with open(f'.data/{symbol}.json', 'r') as cache_file:
                cache_data = cache_file.read()
                all_data = json.loads(cache_data)
        except FileNotFoundError:
            with open(f'.data/{symbol}.json', 'w') as cache_file:
                cache_file.write(json.dumps(all_data))
        except json.decoder.JSONDecodeError:
            all_data = {}
        return all_data

    def read_cache(self, symbol, signal_name):
        """
        Read the cache data from the cache file (symbol.cache) present under the .data folder for the ticker
        :return: Cache data for the given key
        """

        all_data = self.__read_all_cache(symbol)

        return all_data.get(signal_name, {})

    def write_cache(self, symbol, signal_name, data={}):
        """
        Write the cache data to the cache file (symbol.cache) present under the .data folder for the ticker
        """

        all_data = self.__read_all_cache(symbol)

        # Update the cache data with the new data
        all_data[signal_name] = data

        # Write the cache data to the cache file which is a JSON file
        with open(f'.data/{symbol}.json', 'w') as cache_file:
            cache_file.write(json.dumps(all_data))

    def compute(self, ticker):
        """
        Generate a signal
        return data is a dictionary with the following keys:
        - signal: The signal generated (Yes/No)
        - kind: The kind of signal generated (Buy/Sell)
        - price: The price at which the signal was generated
        - timestamp: The timestamp at which the signal was generated
        - message: A message describing the signal
        -**kwargs: Additional data
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def compute_and_plot(self, ticker):
        """
        Cmopute & Plot the signal
        """
        raise NotImplementedError("Subclasses must implement this method")