from discord.ext import commands
from discord import app_commands


class Math(app_commands.Group):
    def __init__(self):
        super().__init__(name="math", description="數學科")


def register(bot: commands.Bot):
    bot.tree.add_command(Math())


