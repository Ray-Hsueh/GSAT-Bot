from discord.ext import commands
from discord import app_commands


class Chinese(app_commands.Group):
    def __init__(self):
        super().__init__(name="chinese", description="國文科")


def register(bot: commands.Bot):
    bot.tree.add_command(Chinese())


