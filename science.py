from discord.ext import commands
from discord import app_commands


class Science(app_commands.Group):
    def __init__(self):
        super().__init__(name="science", description="自然科")


def register(bot: commands.Bot):
    bot.tree.add_command(Science())


