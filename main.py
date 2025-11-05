#!/usr/bin/env python3

from discord.ext import commands
import discord
import config
import os
from keepAlive import keep_alive
import traceback
from dotenv import load_dotenv
load_dotenv()

class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=config.PREFIX, intents=intents, **kwargs)

    async def setup_hook(self):
        for cog in config.cogs:
            try:
                await self.load_extension(cog)
            except Exception as exc:
              error_message = traceback.format_exc()
              print(f'Could not load extension {cog} due to {exc.__class__.__name__}: {exc}')
              print(error_message) 
              
    async def on_ready(self):
        print(f'Logged on as {bot.user} (ID: {bot.user.id})')
        await bot.change_presence(activity=discord.Game('Minecraft'))
        await self.tree.sync()

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have the permissions to execute this command.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command Not Found.")

intents = discord.Intents.default()
intents.message_content = True
bot = Bot(intents=intents)
bot.remove_command('help')

keep_alive()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN not found in .env file")
bot.run(TOKEN)
