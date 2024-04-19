import asyncio
import os
import discord
from discord.ext import tasks, commands

from datetime import datetime
from pytz import timezone

from module.trade.ticker_ai import TickerAI


#-----------------------------------------------------------
# Monitor for a user message in a channel
# When the user mention the bot and asked for a question
# The bot will reply with the answer
#-----------------------------------------------------------

class AIExecutionTask(commands.Cog):
    def __init__(self, bot, DISCORD_AI_CHANNEL_ID):
        self.bot = bot
        self.DISCORD_AI_CHANNEL_ID = DISCORD_AI_CHANNEL_ID

    async def cog_unload(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # check if the message is from a specific channel
        if message.channel.id != self.DISCORD_AI_CHANNEL_ID:
            return

        if self.bot.user.mentioned_in(message):
            try:
                print("Question: ", message.content)          
                ticker_ai = TickerAI()
                response = ticker_ai.chat(message.content)
                await message.channel.send(response)

            except Exception as e:
                print(f"Error: {e}")
                await message.channel.send("I am sorry, I am unable to answer that question at the moment.")

