import discord
from discord.ext import commands
import pandas as pd
import random
import json
import asyncio
import os
from datetime import datetime, timedelta
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='', intents=intents)

def load_vocabulary():
    """載入學測6000字資料"""
    try:
        df = pd.read_csv('學測6000字.csv')
        df = df.dropna(subset=['單字', '級別'])
        return df
    except Exception as e:
        print(f"載入單字資料時發生錯誤: {e}")
        return pd.DataFrame()

def init_gemini():
    """初始化Gemini API"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("請設定GEMINI_API_KEY環境變數")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-lite')

vocabulary_df = load_vocabulary()
gemini_model = init_gemini()

user_games = {}

class GameState:
    def __init__(self, user_id: int, total_questions: int, level: Optional[int] = None):
        self.user_id = user_id
        self.total_questions = total_questions
        self.level = level
        self.current_question = 0
        self.selected_words = []
        self.questions = []
        self.score = 0
        self.start_time = datetime.now()
        self.timeout_task = None
        
    def is_expired(self) -> bool:
        """檢查是否超過3分鐘"""
        return datetime.now() - self.start_time > timedelta(minutes=3)

def select_words(df: pd.DataFrame, count: int, level: Optional[int] = None) -> List[str]:
    """選擇要測試的單字"""
    if df.empty:
        return []
    
    if level:
        filtered_df = df[df['級別'] == level]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return []
    
    selected = filtered_df.sample(n=min(count, len(filtered_df)), random_state=None)
    words = []
    
    for word in selected['單字']:
        if '/' in word:
            word = random.choice(word.split('/'))
        words.append(word)
    
    return words

def generate_question_prompt(words: List[str]) -> str:
    """生成題目的prompt"""
    words_str = '、'.join(words)
    return f"""你是一個英文科測驗命題者，你的任務是為台灣的大學學測（GSAT）出題。要測試用戶是否學會這幾個單字：{words_str}，請你依照學測大考中心的宗旨和難度出題並提供答案和解析，每一個單字只需要出一題，並請確保每個題目只有四個選項，而且正確答案的ABCD是隨機分布的，不可以有明顯規律。選項必須符合台灣學測程度，每一題的每一個選項都應該獨一無二不能重複。正確選項必須是唯一完全符合文意的選項，錯誤選項必須符合詞性但是放入後會造成語意錯誤或不自然或與題幹衝突或不合理或不符合語境。
請以json格式回答並且只需要題號、題目、選項、答案、詳解欄位，其他一概不需要，詳解請用繁體中文表達。以下為你應該遵照的json格式，詳解部分不一定要按照這個格式。
 {{
    "題號": 6,
    "題目": "The company implemented a new employee ______ program to ensure fair career development opportunities for everyone.",
    "選項": {{
      "A": "qualification",
      "B": "rotation",
      "C": "surpass",
      "D": "analysis"
    }},
    "答案": "B",
    "詳解": "句意為「該公司實施了新的員工______計畫，以確保每個人都有公平的職涯發展機會。」空格處應填入名詞，指公司計畫的一種形式。選項(A) qualification (資格)、(C) surpass (超越，為動詞)、(D) analysis (分析) 均不符合語意。選項(B) rotation (輪調、輪職) 符合語意，表示員工輪調計畫，讓員工有機會在不同職位上發展。"
  }} 

以下為學測題目，讓你可以參考著出題，不要把這些例題列出輸出的json中。 
If you put a ______ under a leaking faucet, you will be surprised at the amount of water collected in 24 hours.
(A) border
(B) timer
(C) container
(D) marker
The local farmers' market is popular as it offers a variety of fresh seasonal ______ to people in the community.
(A) produce
(B) fashion
(C) brand
(D) trend
As the years have passed by, many of my childhood memories are already ______; I can no longer recall clearly what happened back then.
(A) blurring
(B) trimming
(C) draining
(D) glaring
Racist remarks are by nature ______ and hurtful, and should be avoided on all occasions.
(A) excessive
(B) furious
(C) offensive
(D) stubborn"""

async def generate_questions(words: List[str]) -> List[Dict]:
    """使用Gemini生成題目"""
    prompt = generate_question_prompt(words)
    
    try:
        response = gemini_model.generate_content(prompt)
        content = response.text.strip()
        
        if content.startswith('```json'):
            content = content[7:-3]
        elif content.startswith('```'):
            content = content[3:-3]
        
        questions_data = json.loads(content)
        
        if isinstance(questions_data, dict):
            return [questions_data]
        return questions_data
        
    except json.JSONDecodeError as e:
        print(f"JSON解析錯誤: {e}")
        print(f"原始內容: {content[:200]}...")
        return []
    except Exception as e:
        print(f"生成題目時發生錯誤: {e}")
        return []

def create_question_embed(question: Dict, question_num: int, total: int) -> discord.Embed:
    """創建題目的Embed"""
    question_text = question['題目'].replace('_', '\\_')
    
    embed = discord.Embed(
        title=f"學測英文詞彙練習 - 第 {question_num}/{total} 題",
        description=question_text,
        color=0x3498db
    )
    
    options = question['選項']
    for key, value in options.items():
        embed.add_field(name=f"({key})", value=value, inline=False)
    
    embed.set_footer(text="請選擇你的答案")
    return embed

def create_result_embed(question: Dict, user_answer: str, is_correct: bool, question_num: int, total: int) -> discord.Embed:
    """創建結果的Embed"""
    color = 0x2ecc71 if is_correct else 0xe74c3c
    status = "✅ 正確！" if is_correct else "❌ 錯誤"
    
    question_text = question['題目'].replace('_', '\\_')
    
    embed = discord.Embed(
        title=f"第 {question_num}/{total} 題結果 - {status}",
        description=question_text,
        color=color
    )
    
    options = question['選項']
    correct_answer = question['答案']
    
    for key, value in options.items():
        if key == correct_answer:
            embed.add_field(name=f"✅ ({key}) (正確答案)", value=value, inline=False)
        elif key == user_answer and not is_correct:
            embed.add_field(name=f"❌ ({key}) (你的答案)", value=value, inline=False)
        else:
            embed.add_field(name=f"({key})", value=value, inline=False)
    
    explanation_text = question['詳解'].replace('_', '\\_')
    embed.add_field(name="詳解", value=explanation_text, inline=False)
    
    return embed


class QuizView(discord.ui.View):
    def __init__(self, question: Dict, question_num: int, total: int, game_state: GameState):
        super().__init__(timeout=180)  # 3分鐘超時
        self.question = question
        self.question_num = question_num
        self.total = total
        self.game_state = game_state
        
        options = question['選項']
        for key, value in options.items():
            button = discord.ui.Button(
                label=f"({key}) {value}",
                style=discord.ButtonStyle.primary
            )
            button.callback = self.create_answer_callback(key)
            self.add_item(button)
        
        stop_button = discord.ui.Button(
            label="停止測驗",
            style=discord.ButtonStyle.danger
        )
        stop_button.callback = self.stop_quiz_callback
        self.add_item(stop_button)
    
    def create_answer_callback(self, answer_key: str):
        async def answer_callback(interaction: discord.Interaction):
            if interaction.user.id != self.game_state.user_id:
                await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
                return
            
            correct_answer = self.question['答案']
            is_correct = answer_key == correct_answer
            
            if is_correct:
                self.game_state.score += 1
            
            is_last_question = self.game_state.current_question + 1 >= self.total
            if is_last_question and self.game_state.user_id in user_games:
                del user_games[self.game_state.user_id]
            
            result_embed = create_result_embed(
                self.question, answer_key, is_correct, 
                self.question_num, self.total
            )

            result_view = discord.ui.View(timeout=180)
            
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label.startswith("("):
                    new_item = discord.ui.Button(
                        label=item.label,
                        style=item.style,
                        disabled=True
                    )
                    result_view.add_item(new_item)
            
            if not is_last_question:
                next_button = discord.ui.Button(
                    label="下一題",
                    style=discord.ButtonStyle.success
                )
                async def next_callback(interaction: discord.Interaction):
                    if interaction.user.id != self.game_state.user_id:
                        await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
                        return
                    
                    for item in self.children:
                        item.disabled = True
                    
                    await interaction.response.edit_message(view=self)
                    
                    self.game_state.current_question += 1
                    
                    if self.game_state.current_question < self.total:
                        next_question = self.game_state.questions[self.game_state.current_question]
                        next_embed = create_question_embed(
                            next_question, 
                            self.game_state.current_question + 1, 
                            self.total
                        )
                        
                        next_view = QuizView(
                            next_question, 
                            self.game_state.current_question + 1, 
                            self.total, 
                            self.game_state
                        )
                        
                        await interaction.followup.send(embed=next_embed, view=next_view)
                    else:
                        if self.game_state.user_id in user_games:
                            del user_games[self.game_state.user_id]
                
                next_button.callback = next_callback
                result_view.add_item(next_button)
            else:
                # 測驗完成，顯示完成按鈕
                stop_button = discord.ui.Button(
                    label="測驗完成",
                    style=discord.ButtonStyle.danger,
                    disabled=True
                )
                result_view.add_item(stop_button)
            
            await interaction.response.edit_message(embed=result_embed, view=result_view)
        
        return answer_callback
    
    async def stop_quiz_callback(self, interaction: discord.Interaction):
        """停止測驗按鈕的回調函數"""
        if interaction.user.id != self.game_state.user_id:
            await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
            return
        
        if self.game_state.user_id in user_games:
            del user_games[self.game_state.user_id]
        
        for item in self.children:
            item.disabled = True
        
        stop_embed = discord.Embed(
            title="測驗已停止",
            description="測驗已被用戶停止。",
            color=0xe74c3c
        )
        
        await interaction.response.edit_message(embed=stop_embed, view=self)
    
    async def next_question_callback(self, interaction: discord.Interaction):
        """下一題按鈕的回調函數"""
        if interaction.user.id != self.game_state.user_id:
            await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        await self.next_question(interaction)
    
    async def next_question(self, interaction: discord.Interaction):
        """處理下一題或結束測驗"""
        self.game_state.current_question += 1
        
        if self.game_state.current_question < self.total:
            next_question = self.game_state.questions[self.game_state.current_question]
            next_embed = create_question_embed(
                next_question, 
                self.game_state.current_question + 1, 
                self.total
            )
            
            next_view = QuizView(
                next_question, 
                self.game_state.current_question + 1, 
                self.total, 
                self.game_state
            )
            
            await interaction.followup.send(embed=next_embed, view=next_view)
        else:
            if self.game_state.user_id in user_games:
                del user_games[self.game_state.user_id]
    
    async def on_timeout(self):
        """超時處理"""
        timeout_embed = discord.Embed(
            title="測驗超時",
            description="測驗已超過3分鐘，自動結束。",
            color=0xe74c3c
        )
        
        for item in self.children:
            item.disabled = True
        
        if self.game_state.user_id in user_games:
            del user_games[self.game_state.user_id]

@bot.event
async def on_ready():
    print(f'{bot.user} 已上線！')
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"同步斜線指令時發生錯誤: {e}")

@bot.tree.command(name="vocabulary", description="開始詞彙測驗")
async def start_quiz(interaction: discord.Interaction, questions: int = 5, level: Optional[int] = None):
    """開始詞彙測驗"""
    if questions < 1 or questions > 20:
        await interaction.response.send_message("題數必須在1-20之間！", ephemeral=True)
        return
    
    if level and (level < 1 or level > 6):
        await interaction.response.send_message("級別必須在1-6之間！", ephemeral=True)
        return
    
    if interaction.user.id in user_games:
        await interaction.response.send_message("你已經有一個進行中的測驗！請先完成或等待超時。", ephemeral=True)
        return
    
    game_state = GameState(interaction.user.id, questions, level)
    user_games[interaction.user.id] = game_state
    
    selected_words = select_words(vocabulary_df, questions, level)
    game_state.selected_words = selected_words
    
    if not interaction.response.is_done():
        await interaction.response.send_message("正在生成題目，請稍候...")

    questions_data = await generate_questions(selected_words)
    
    if not questions_data:
        await interaction.followup.send("生成題目時發生錯誤，請稍後再試。", ephemeral=True)
        del user_games[interaction.user.id]
        return
    
    game_state.questions = questions_data
    
    first_question = questions_data[0]
    embed = create_question_embed(first_question, 1, questions)
    view = QuizView(first_question, 1, questions, game_state)
    
    try:
        await interaction.edit_original_response(content="", embed=embed, view=view)
    except discord.errors.NotFound:
        if interaction.user.id in user_games:
            del user_games[interaction.user.id]
        await interaction.followup.send("互動已超時，請重新開始測驗。", ephemeral=True)


@bot.tree.command(name="help", description="顯示幫助資訊")
async def help_command(interaction: discord.Interaction):
    """顯示幫助資訊"""
    embed = discord.Embed(
        title="學測英文練習機器人",
        description="幫助你練習學測英文",
        color=0x3498db
    )
    
    embed.add_field(
        name="指令",
        value="""`/vocabulary [題數] [級別]` - 開始測驗
`/help` - 顯示此幫助""",
        inline=False
    )
    
    embed.add_field(
        name="參數說明",
        value="""題數：1-20題（預設5題）
級別：1-6級（可選，不指定則隨機選擇）""",
        inline=False
    )
    
    embed.add_field(
        name="注意事項",
        value="• 每題有3分鐘時間限制\n• 使用按鈕選擇答案\n• 可隨時點擊「停止測驗」按鈕結束\n• 每題結束後都會顯示詳細解析",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
