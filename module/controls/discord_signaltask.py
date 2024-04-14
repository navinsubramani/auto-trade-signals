import asyncio
import os
import discord
from discord.ext import tasks, commands

from module.flow.generate_indicator import GenerateIndicator

DATA_RANAGE_DAYS = int(os.getenv('DATA_RANAGE_DAYS'))
DATA_INTERVAL_MINUTES = int(os.getenv('DATA_INTERVAL_MINUTES'))
LOOP_INTERVAL_SECONDS = int(os.getenv('LOOP_INTERVAL_SECONDS'))

#-----------------------------------------------------------
#----------------- Discord Signal Task Class ---------------
#-----------------------------------------------------------
class SignalExecutionTask(commands.Cog):
    def __init__(self, bot, signal_channel_id):
        self.bot = bot
        self.signal_channel_id = signal_channel_id
        self.lock = asyncio.Lock()
        self.gi = GenerateIndicator(
            DATA_RANAGE_DAYS,
            DATA_INTERVAL_MINUTES
        )
        self.signal_executor.start()
        self.status.start()

    async def cog_unload(self):
        self.signal_executor.cancel()
        self.status.cancel()

    async def execute_signal(self):
        print("***Executing signal Task***")
        await self.gi.execute_gi(self.publish_signal)
    
    #---------------------------------------------
    #-------- Signal Executor Task Loop ----------
    #---------------------------------------------
    @tasks.loop(seconds=LOOP_INTERVAL_SECONDS)
    async def signal_executor(self):
        async with self.lock:
            await self.execute_signal()

    @signal_executor.before_loop
    async def before_signal_executor(self):
        await self.bot.wait_until_ready()

    @signal_executor.after_loop
    async def after_signal_executor(self):
        if self.signal_executor.is_being_cancelled():
            print("Signal Executor Task Loop is cancelled.")
        else:
            print("Signal Executor Task Loop is completed.")

    async def publish_signal(self, signal, buf=None):
        print(f"Publishing Signal:")
        try:
            embed = discord.Embed(
                title=f"{signal['symbol']} : {signal['name']}",
                description=signal["message"],
                color=discord.Color.blue()
            )

            if buf is not None:
                # Send the image through Discord in an embed
                file = discord.File(buf, filename="plot.png")
                embed.set_image(url="attachment://plot.png")  # Use attachment:// to refer to uploaded files

                # Send the signal and tag everyone
                await self.bot.get_channel(self.signal_channel_id).send(embed=embed, content="@everyone", file=file)
            else:
                await self.bot.get_channel(self.signal_channel_id).send(embed=embed, content="@everyone")
        except Exception as e:
            print(f"Failed to publish signal: {e}")

    #---------------------------------------------
    #------------ Signal Task Commands -----------
    #---------------------------------------------
    @commands.command()
    async def add(self, ctx, symbol: str):
        async with self.lock:
            result = self.gi.add_symbol(symbol)
            await ctx.reply(f"{result['message']}")

    @commands.command()
    async def remove(self, ctx, symbol: str):
        async with self.lock:
            result = self.gi.remove_symbol(symbol)
            await ctx.reply(f"{result['message']}")

    @commands.command(name='list')
    async def list(self, ctx):
        async with self.lock:
            ticker_list = self.gi.Ticker_Manager.get_all_tickers().keys()
            ticker_list = ' | '.join(ticker_list)
            await ctx.reply(f"{ticker_list}")

    @tasks.loop(seconds=3600)
    async def status(self):
        await self.bot.get_channel(self.signal_channel_id).send(content="I am still alive!")