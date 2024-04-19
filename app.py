from dotenv import load_dotenv
import os
import discord
from discord.ext import commands

load_dotenv(override=True)

from module.controls.discord_signaltask import SignalExecutionTask
from module.controls.discord_aitask import AIExecutionTask

#---------------------------------------------
#------------ Setup Discord Bot --------------
#---------------------------------------------

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_SIGNAL_CHANNEL_ID = int(os.getenv('DISCORD_SIGNAL_CHANNEL_ID'))
DISCORD_AI_CHANNEL_ID = int(os.getenv('DISCORD_AI_CHANNEL_ID'))

print(f"DISCORD_BOT_TOKEN: {DISCORD_BOT_TOKEN}")
print(f"DISCORD_SIGNAL_CHANNEL_ID: {DISCORD_SIGNAL_CHANNEL_ID}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load the cog when the bot starts
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    await bot.add_cog(SignalExecutionTask(bot, DISCORD_SIGNAL_CHANNEL_ID))
    await bot.add_cog(AIExecutionTask(bot, DISCORD_AI_CHANNEL_ID))
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    finally:
        pass

bot.run(DISCORD_BOT_TOKEN)
