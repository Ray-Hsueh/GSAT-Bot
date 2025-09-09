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
    #chinese.register(bot)
    #subject_math.register(bot)
    #science.register(bot)
    social.register(bot)


if __name__ == "__main__":
    register_subjects()
    
    @bot.tree.command(name="help", description="顯示幫助資訊")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="GSAT 學測練習機器人",
            description="",
            color=0x3498db
        )
        embed.add_field(
            name="英文",
            value="""`/english vocabulary [題數] [級別]` - 英文詞彙測驗
`/english comprehensive` - 英文綜合測驗（完測後公布詳解）""",
            inline=False
        )
        embed.add_field(
            name="其他科目",
            value="`/social choice [questions] [subject]` - 社會科單選題（逐題作答）\nsubject 可選：歷史/地理/公民（可省略）",
            inline=False
        )
        embed.add_field(
            name="參數說明（英文詞彙）",
            value="""題數：1-20（預設5）
級別：1-6（可省略，未指定則從所有級別挑選）""",
            inline=False
        )
        embed.add_field(
            name="注意事項",
            value="• 詞彙每題 3 分鐘；綜合 5 分鐘\n• 使用按鈕選擇答案\n• 可隨時點擊「停止測驗」結束",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    bot.run(os.getenv('DISCORD_TOKEN'))


