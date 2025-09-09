import os
import socket
import platform
import discord
from discord import app_commands
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
        top_level_cmds = bot.tree.get_commands()
        invokable_total = 0
        for cmd in top_level_cmds:
            if isinstance(cmd, app_commands.Group):
                invokable_total += len(cmd.commands)
            else:
                invokable_total += 1
        print(f"已同步 {len(synced)} 個頂層指令/群組；可用指令總數（含子指令）= {invokable_total}")
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
            name="指令",
            value="""`/english vocabulary [questions] [level]` - 英文詞彙測驗
`/english comprehensive` - 英文綜合測驗
`/social choice [questions] [subject]` - 社會科單選題""",
            inline=False
        )
        embed.add_field(
            name="參數說明",
            value="""questions：題數（英文 1-20；社會 1-10；預設 5）
level：英文等級 1-6（可不選，未指定則從所有級別挑選）
subject：社會科別（歷史/地理/公民）""",
            inline=False
        )
        embed.add_field(
            name="注意事項",
            value="• 英文詞彙每題 3 分鐘；英文綜合 5 分鐘\n• 社會科每題 3 分鐘\n• 使用按鈕選擇答案\n• 可隨時點擊「停止測驗」結束",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="about", description="關於這個機器人")
    async def about_command(interaction: discord.Interaction):
        latency_ms = int(round(bot.latency * 1000)) if bot.latency is not None else -1
        host_info = f"{platform.system()} {platform.release()} • {socket.gethostname()}"
        embed = discord.Embed(
            title="關於 GSAT 學測練習機器人",
            description="幫助同學練習各科題目，支援逐題按鈕作答與詳解顯示",
            color=0x2ecc71
        )
        embed.add_field(
            name="它在做什麼",
            value="""使用 `/help` 可以查看指令列表""",
            inline=False
        )
        embed.add_field(
            name="怎麼做到的",
            value="""透過 Google Gemini 2.5 Flash Lite 技術支援以產生題目、選項與詳解""",
            inline=False
        )
        embed.add_field(
            name="也歡迎試試我的其他機器人",
            value="""- [捷運球](https://discord.com/oauth2/authorize?client_id=1221349350425493504&permissions=1126726688427072&integration_type=0&scope=bot)
- [政客迷因](https://discord.com/oauth2/authorize?client_id=1400469248869924964)""",
            inline=False
        )
        embed.add_field(
            name="系統與延遲",
            value=f"主機：{host_info}\n位置：Helsinki, Finland\n延遲：{latency_ms} ms",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
    bot.run(os.getenv('DISCORD_TOKEN'))


