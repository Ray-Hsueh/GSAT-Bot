import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

import english
import chinese
import subject_math
import science
import social


intents = discord.Intents.default()
bot = commands.Bot(command_prefix='', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user} 已上線！')
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"同步斜線指令時發生錯誤: {e}")


def register_subjects():
    english.register(bot)
    chinese.register(bot)
    subject_math.register(bot)
    science.register(bot)
    social.register(bot)


if __name__ == "__main__":
    register_subjects()
    bot.run(os.getenv('DISCORD_TOKEN'))


