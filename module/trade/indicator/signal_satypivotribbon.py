from module.trade.signals import SignalBase

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
import io

class SignalSatypePivotRibbon(SignalBase):
    """
    Multiple Time Frame Analysis: The time_warp input allows traders to switch between various time frames, facilitating analysis across different market conditions without needing to manually adjust the settings for each chart.
    EMA Settings: There are settings for a fast, pivot, and slow EMA. The script also includes additional EMAs termed as 'fast conviction EMA' and 'slow conviction EMA' which seem to provide signals for market conviction in the trend direction.
    Visual Cues (Clouds and Highlights): The script plots EMAs and fills the space between certain EMAs with colored "clouds" to visually represent different market conditions (bullish or bearish). Highlights can be toggled for individual EMAs to emphasize them further.
    Conviction Arrows: These are plotted to indicate changes in trend based on the crossover of the conviction EMAs. This feature can be toggled on or off.
    Candle Bias: The script optionally modifies the color of the candlesticks based on their position relative to a bias EMA, adding another layer of trend indication.
    """

    def __init__(self, fast_ema=8, pivot_ema=21, slow_ema=34, fast_conviction_ema=13, slow_conviction_ema=48, bias_ema=21):
        super().__init__()
        # Apply EMA calculations
        self.signal_name = "EMA_Reversal"
        self.fast_ema = fast_ema
        self.pivot_ema = pivot_ema
        self.slow_ema = slow_ema
        self.fast_conviction_ema = fast_conviction_ema
        self.slow_conviction_ema = slow_conviction_ema
        self.bias_ema = bias_ema

    def __calculate_ema(self, prices, period):
        """
        Calculate the Exponential Moving Average for the given prices
        :param prices: Prices for which the EMA needs to be calculated
        :param period: Period for which the EMA needs to be calculated
        :return: EMA for the given prices
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    def compute(self, ticker):
        
        # Get the historical data for the ticker
        df = ticker.historical_data

        # Calculate the EMAs
        df['Fast_EMA'] = self.__calculate_ema(df['Close'], self.fast_ema)
        df['Pivot_EMA'] = self.__calculate_ema(df['Close'], self.pivot_ema)
        df['Slow_EMA'] = self.__calculate_ema(df['Close'], self.slow_ema)
        df['Fast_Conviction_EMA'] = self.__calculate_ema(df['Close'], self.fast_conviction_ema)
        df['Slow_Conviction_EMA'] = self.__calculate_ema(df['Close'], self.slow_conviction_ema)
        df['Bias_EMA'] = self.__calculate_ema(df['Close'], self.bias_ema)

        # Determine bullish or bearish conviction
        df['Bullish_Conviction'] = df['Fast_Conviction_EMA'] > df['Slow_Conviction_EMA']
        df['Bearish_Conviction'] = df['Fast_Conviction_EMA'] < df['Slow_Conviction_EMA']

        # Determine bullish or bearish trend
        cache = self.read_cache(ticker.symbol, self.signal_name)
        pivot_last_state = cache.get("pivot_last_state", None)
        conviction_last_state = cache.get("conviction_last_state", None)
        #print(cache)


        row = df.iloc[-1]

        # find conviction based on pivot EMA (21)
        # Check the state of last element in df.itemrows() and compare with the current state
        pivot_current_state = pivot_last_state
        if row['Fast_EMA'] >= row['Pivot_EMA'] and row['Pivot_EMA'] >= row['Slow_EMA']:
            pivot_current_state = "bullish_cloud"
        elif row['Fast_EMA'] < row['Pivot_EMA'] and row['Pivot_EMA'] <= row['Slow_EMA']:
            pivot_current_state = "bearish_cloud"

        # find conviction based on bias EMA (13 & 48)
        # Check the state of last element in df.itemrows() and compare with the current state
        conviction_current_state = conviction_last_state
        if row["Bullish_Conviction"]:
            conviction_current_state = "bullish"
        elif row["Bearish_Conviction"]:
            conviction_current_state = "bearish"

        # If one of the pivot state changes, then it is a signal
        if pivot_last_state != pivot_current_state or conviction_last_state != conviction_current_state:
            cache["pivot_last_state"] = pivot_current_state
            cache["conviction_last_state"] = conviction_current_state
            self.write_cache(ticker.symbol, self.signal_name, cache)
            #print(cache)

            sentiment = "Buy" if pivot_current_state == "bullish_cloud" else "Sell"

            return {
                "signal": True,
                "name": self.signal_name,
                "symbol": ticker.symbol,
                "kind": sentiment,
                "price": row['Close'],
                "timestamp": row.name,
                "message": f"""
Signal generated based on Saty Pivot Ribbon strategy indicating that there is a reversal occured.
Stock: {ticker.symbol}
Price: {row['Close']}
Timestamp: {row.name}
Sentiment: {sentiment}
Pivot State {self.fast_ema}ema, {self.pivot_ema}ema, {self.fast_ema}ema: {pivot_current_state}
Conviction State {self.fast_conviction_ema}ema & {self.slow_conviction_ema}ema: {conviction_current_state}
""",
            }
        
        return {
            "signal": False,
            "name": self.signal_name,
            "symbol": ticker.symbol,
            "kind": None,
            "price": None,
            "timestamp": None,
            "message": None,
        }
    
    def compute_and_plot(self, ticker):
        """
        Compute & Plot the signal
        """
        # Get the historical data for the ticker
        df = ticker.historical_data

        # Calculate the EMAs
        df['Fast_EMA'] = self.__calculate_ema(df['Close'], self.fast_ema)
        df['Pivot_EMA'] = self.__calculate_ema(df['Close'], self.pivot_ema)
        df['Slow_EMA'] = self.__calculate_ema(df['Close'], self.slow_ema)
        df['Fast_Conviction_EMA'] = self.__calculate_ema(df['Close'], self.fast_conviction_ema)
        df['Slow_Conviction_EMA'] = self.__calculate_ema(df['Close'], self.slow_conviction_ema)
        df['Bias_EMA'] = self.__calculate_ema(df['Close'], self.bias_ema)

        # Determine bullish or bearish conviction
        df['Bullish_Conviction'] = df['Fast_Conviction_EMA'] > df['Slow_Conviction_EMA']
        df['Bearish_Conviction'] = df['Fast_Conviction_EMA'] < df['Slow_Conviction_EMA']

        # From the dataframe, get only the last 80 elements as a sample dataframe
        # Remove the Index
        df = df.tail(80)
        df.reset_index(inplace=True)

        # Plotting
        fig, ax = plt.subplots(figsize=(15, 10))

        # Plot EMAs
        ax.plot(df.index, df['Close'], label='Close Price', color='black', alpha=0.3)
        ax.plot(df.index, df['Fast_EMA'], label='Fast EMA (8)', color='green')
        ax.plot(df.index, df['Pivot_EMA'], label='Pivot EMA (21)', color='blue')
        ax.plot(df.index, df['Slow_EMA'], label='Slow EMA (34)', color='red')

        # Fill between EMAs to create 'clouds'
        ax.fill_between(df.index, df['Fast_EMA'], df['Pivot_EMA'], where=(df['Fast_EMA'] >= df['Pivot_EMA']), facecolor='green', alpha=0.5, label='Bullish Fast Cloud')
        ax.fill_between(df.index, df['Fast_EMA'], df['Pivot_EMA'], where=(df['Fast_EMA'] < df['Pivot_EMA']), facecolor='red', alpha=0.5, label='Bearish Fast Cloud')
        ax.fill_between(df.index, df['Pivot_EMA'], df['Slow_EMA'], where=(df['Pivot_EMA'] >= df['Slow_EMA']), facecolor='blue', alpha=0.5, label='Bullish Slow Cloud')
        ax.fill_between(df.index, df['Pivot_EMA'], df['Slow_EMA'], where=(df['Pivot_EMA'] < df['Slow_EMA']), facecolor='orange', alpha=0.5, label='Bearish Slow Cloud')

        # Plot conviction based on pivot EMA (21)
        pivot_last_state = None
        for date, row in df.iterrows():
            if row['Fast_EMA'] >= row['Pivot_EMA'] and row['Pivot_EMA'] >= row['Slow_EMA'] and pivot_last_state != 'bullish cloud':
                ax.annotate('Bullish Clouds', xy=(date, row['Slow_EMA']), xytext=(date, row['Slow_EMA'] * 0.995), arrowprops=dict(facecolor='green', shrink=0.005))
                pivot_last_state = 'bullish cloud'
            elif row['Fast_EMA'] < row['Pivot_EMA'] and row['Pivot_EMA'] < row['Slow_EMA'] and pivot_last_state != 'bearish cloud':
                ax.annotate('Bearish Clouds', xy=(date, row['Slow_EMA']), xytext=(date, row['Slow_EMA'] * 1.005), arrowprops=dict(facecolor='red', shrink=0.005))
                pivot_last_state = 'bearish cloud'

        # Plot Conviction Arrows based on 13 & 48 EMA
        last_state = None
        for date, row in df.iterrows():
            # find if it is currently bullish or bearish and only when there is a state change from last, make a annotation
            if row['Bullish_Conviction'] and last_state != 'bullish':
                ax.annotate('Bullish Conviction', xy=(date, row['Slow_EMA']), xytext=(date, row['Slow_EMA'] * 0.995), arrowprops=dict(facecolor='green', shrink=0.005))
                last_state = 'bullish'
            elif row['Bearish_Conviction'] and last_state != 'bearish':
                ax.annotate('Bearish Conviction', xy=(date, row['Fast_EMA']), xytext=(date, row['Fast_EMA'] * 1.005), arrowprops=dict(facecolor='red', shrink=0.005))
                last_state = 'bearish'


        # Candlestick bias coloring (as bars for simplicity)
        #ax.bar(df.index, df['Close'] - df['Open'], bottom=df['Open'], color=df.apply(lambda row: 'green' if row['Close'] > row['Bias_EMA'] else 'red', axis=1), zorder=3)

        # Final plot adjustments
        #timezone = pytz.timezone("America/New_York")
        #ax.xaxis.set_major_locator(plt.MaxNLocator(15))
        #ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.DateFormatter('%m-%d - %H:%M', tz=timezone)))
        ax.legend()
        plt.xticks(rotation=45)
        plt.title('Saty Pivot Ribbon Simulation')
        plt.xlabel('Sample Data Index')
        plt.ylabel('Price')
        plt.grid(True)
        #plt.show()
        
        # Save the plot to a BytesIO object
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)  # Rewind the buffer to the beginning so it can be read from
        plt.close()  # Close the plot figure to free up memory

        return {
            "buf": buf
        }