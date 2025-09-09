from discord.ext import commands
from discord import app_commands


class Social(app_commands.Group):
    def __init__(self):
        super().__init__(name="social", description="社會科")


def register(bot: commands.Bot):
    bot.tree.add_command(Social())


