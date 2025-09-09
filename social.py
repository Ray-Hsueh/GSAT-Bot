from discord.ext import commands
from discord import app_commands
import discord
import os
import random
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Optional


SOCIAL_EXAMPLES = (
    "甲和乙兩人在溪邊戲水，乙不慎落水，甲會游泳但見溪流湍急未下水救援，後乙不幸溺斃。\n"
    "恰巧有路人在高處錄下影片上傳網路，引發輿論一片譁然，並要求檢察官起訴甲。也有\n"
    "部分網民主張修法，將此種行為入罪化。依刑法基本原則判斷，偵辦此案的檢察官\n"
    "最可能如何判定是否起訴？\n"
    "(A)依從舊原則，僅能依現行法律辦理起訴事宜\n"
    "(B)因犯行明確，可逕行起訴甲再啟動修法程序\n"
    "(C)因犯行明確，故可以類推適用類似法條起訴\n"
    "(D)依罪刑法定，須依據新修正的法律來起訴甲\n\n"
    "1814 年，英人萊佛士造訪爪哇島上建於約八、九世紀的佛教遺址，看到許多巨大的\n"
    "佛塔，塔上飾以千幅的浮雕作品及數百尊佛陀雕像。此遺址形成的背景最可能是：\n"
    "(A)越南接受從西域直接傳來的佛教，再傳往當地\n"
    "(B)唐朝派遣使節前往當地傳播佛教時，雕塑佛像\n"
    "(C)日本派遣僧侶前往當地推廣佛教時，建造佛塔\n"
    "(D)印度人將佛教傳播到當地，影響其建築與雕塑\n\n"
    "全球各殖民地在獨立後，有些殖民地成為富國，有些卻深陷貧窮。對此，某書指出\n"
    "「北美、澳紐等地區，原為人口相對稀少且技術較落後，被殖民後，經濟快速成長。\n"
    "中南美洲人口相對密集，但被殖民後，到近代卻發展遲緩。」該書從體制、自然環境、\n"
    "人口密度與人口移動等角度，解釋上述殖民地獨立後呈現經濟發展不均的現象。下列\n"
    "何者最能解釋該書的說法？\n"
    "(A)英國法制較注重個人財產權，有助繼承制度的北美與澳紐人民勇於投資\n"
    "(B)西、葡種植咖啡需大量資金，使得中南美洲的此類栽培業擁有較多企業\n"
    "(C)黃熱病、瘧疾容易導致死亡，因而屬於熱帶氣候區的殖民地較缺乏勞力\n"
    "(D)古文明地區環境負載力較低，促使地處於古文明的殖民地發展較為遲緩\n"
)

def _init_gemini():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError('請設定GEMINI_API_KEY環境變數')
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-lite')


def _load_curriculum() -> List[str]:
    path = '高中必修社會課綱.csv'
    if not os.path.exists(path):
        return []
    try:
        entries: List[str] = []
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                parts = [p.strip() for p in raw.split(',')]
                for p in parts:
                    if p:
                        entries.append(p)
        return entries
    except Exception:
        return []


def _build_prompt(curr_items: List[str], num_questions: int) -> str:
    items_text = '\n'.join([f"- {it}" for it in curr_items])
    return (
        "你是社會科測驗命題者，你的任務是為台灣大學學測（GSAT）設計風格多元的社會科單選題目，題目必須學測大考中心的宗旨和難度出題並提供答案和解析，並且融入時事題、素養題等元素，一個題目只能包含題目文本、選項、解答、解析。不要出需要看圖片的題目、也不要在選項中寫出很好判斷的答案，每一題都只有四個選項而且正確答案的選項位置是隨機分布無規律，每個選項都要有足夠的鑑別度，請絕對要參考學測題目，課綱內容應該是題目背後要考的意涵，不要出現在選項中，正確選項只能有一個。\n"
        "以下為本次我希望測驗的課綱：\n"
        f"{items_text}\n\n"
        "以下為學測社會題型參考（請模仿風格但不要複製，也不要把這些例題出現在輸出中）：\n"
        f"{SOCIAL_EXAMPLES}\n"
        "請你依照上述課綱，產生"
        f"{num_questions}"
        "題社會科單選題，並以JSON陣列輸出。每個元素需為：{\"題目\": string, \"選項\": {\"A\": string, \"B\": string, \"C\": string, \"D\": string}, \"答案\": \"A/B/C/D\", \"解析\": string}。不要輸出任何多餘文字或代碼框。"
    )


def _parse_model_json(text: str) -> List[Dict]:
    content = text.strip()
    if content.startswith('```json'):
        content = content[7:-3]
    elif content.startswith('```'):
        content = content[3:-3]
    data = json.loads(content)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def _create_question_embed(q: Dict, idx: int, total: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"社會科單選題 - 第 {idx}/{total} 題",
        description=q.get('題目', ''),
        color=0x1abc9c
    )
    options = q.get('選項', {})
    for key in ['A', 'B', 'C', 'D']:
        if key in options:
            embed.add_field(name=f"({key})", value=str(options[key]), inline=False)
    embed.set_footer(text="請選擇你的答案")
    return embed


def _create_result_embed(q: Dict, user_answer: str, is_correct: bool, idx: int, total: int) -> discord.Embed:
    color = 0x2ecc71 if is_correct else 0xe74c3c
    status = "✅ 正確！" if is_correct else "❌ 錯誤"
    embed = discord.Embed(
        title=f"第 {idx}/{total} 題結果 - {status}",
        description=q.get('題目', ''),
        color=color
    )
    options = q.get('選項', {})
    correct = q.get('答案')
    for key in ['A', 'B', 'C', 'D']:
        if key in options:
            if key == correct:
                embed.add_field(name=f"✅ ({key}) (正確答案)", value=str(options[key]), inline=False)
            elif key == user_answer and not is_correct:
                embed.add_field(name=f"❌ ({key}) (你的答案)", value=str(options[key]), inline=False)
            else:
                embed.add_field(name=f"({key})", value=str(options[key]), inline=False)
    expl = q.get('解析', '')
    if expl:
        embed.add_field(name="解析", value=str(expl), inline=False)
    return embed


class SocialState:
    def __init__(self, user_id: int, questions: List[Dict]):
        self.user_id = user_id
        self.questions = questions
        self.total = len(questions)
        self.index = 0
        self.score = 0


social_games: Dict[int, SocialState] = {}


class SocialQuizView(discord.ui.View):
    def __init__(self, state: SocialState):
        super().__init__(timeout=180)
        self.state = state
        q = self.state.questions[self.state.index]
        options = q.get('選項', {})
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                btn = discord.ui.Button(label=f"({key})", style=discord.ButtonStyle.primary)
                btn.callback = self._make_cb(key)
                self.add_item(btn)
        stop_btn = discord.ui.Button(label="停止測驗", style=discord.ButtonStyle.danger)
        stop_btn.callback = self._stop_cb
        self.add_item(stop_btn)

    def _make_cb(self, answer_key: str):
        async def _cb(interaction: discord.Interaction):
            if interaction.user.id != self.state.user_id:
                await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
                return
            q = self.state.questions[self.state.index]
            correct = str(q.get('答案', '')).strip()
            is_correct = (answer_key.strip() == correct)
            if is_correct:
                self.state.score += 1
            result_view = discord.ui.View(timeout=180)
            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.label.startswith("("):
                    result_view.add_item(discord.ui.Button(label=item.label, style=item.style, disabled=True))
            is_last = (self.state.index + 1 >= self.state.total)
            if not is_last:
                next_btn = discord.ui.Button(label="下一題", style=discord.ButtonStyle.success)
                async def _next(interaction: discord.Interaction):
                    if interaction.user.id != self.state.user_id:
                        await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
                        return
                    next_btn.disabled = True
                    await interaction.response.edit_message(view=result_view)
                    self.state.index += 1
                    if self.state.index < self.state.total:
                        nq = self.state.questions[self.state.index]
                        embed = _create_question_embed(nq, self.state.index + 1, self.state.total)
                        view = SocialQuizView(self.state)
                        await interaction.followup.send(embed=embed, view=view)
                    else:
                        social_games.pop(self.state.user_id, None)
                next_btn.callback = _next
                result_view.add_item(next_btn)
            else:
                done_btn = discord.ui.Button(label="測驗完成", style=discord.ButtonStyle.danger, disabled=True)
                result_view.add_item(done_btn)
                social_games.pop(self.state.user_id, None)
            embed = _create_result_embed(q, answer_key, is_correct, self.state.index + 1, self.state.total)
            await interaction.response.edit_message(embed=embed, view=result_view)
        return _cb

    async def _stop_cb(self, interaction: discord.Interaction):
        if interaction.user.id != self.state.user_id:
            await interaction.response.send_message("這不是你的測驗！", ephemeral=True)
            return
        social_games.pop(self.state.user_id, None)
        for item in self.children:
            item.disabled = True
        stop_embed = discord.Embed(title="測驗已停止", description="測驗已被用戶停止。", color=0xe74c3c)
        await interaction.response.edit_message(embed=stop_embed, view=self)

    async def on_timeout(self):
        social_games.pop(self.state.user_id, None)


class Social(app_commands.Group):
    def __init__(self):
        super().__init__(name="social", description="社會科")
        self._model = _init_gemini()
        self._curriculum = _load_curriculum()

    @app_commands.command(name="choice", description="開始社會科單選題測驗")
    @app_commands.describe(subject="選擇社會科別：歷史/地理/公民")
    @app_commands.choices(subject=[
        app_commands.Choice(name="歷史", value="歷"),
        app_commands.Choice(name="地理", value="地"),
        app_commands.Choice(name="公民", value="公"),
    ])
    async def choice(self, interaction: discord.Interaction, questions: int = 5, subject: Optional[str] = None):
        if questions < 1 or questions > 10:
            await interaction.response.send_message("題數需在 1-10 之間。", ephemeral=True)
            return
        if interaction.user.id in social_games:
            await interaction.response.send_message("你已經有一個進行中的社會科測驗！", ephemeral=True)
            return
        if not self._curriculum:
            await interaction.response.send_message("找不到課綱資料檔案：高中必修社會課綱.csv", ephemeral=True)
            return
        lines = self._curriculum
        if subject:
            lines = [ln for ln in lines if ln.startswith(subject)]
            if not lines:
                await interaction.response.send_message("此科別的課綱資料為空，請改選其他科別或移除限制。", ephemeral=True)
                return
        sample_items = random.sample(lines, k=min(5, len(lines)))
        prompt = _build_prompt(sample_items, questions)
        if not interaction.response.is_done():
            subject_map = {"歷": "歷史", "地": "地理", "公": "公民"}
            subject_text = subject_map.get(subject, None) if subject else None
            if subject_text:
                await interaction.response.send_message(f"正在生成{subject_text}科題目，請稍候...")
            else:
                await interaction.response.send_message("正在生成社會科題目，請稍候...")
        try:
            resp = self._model.generate_content(prompt)
            data = _parse_model_json(resp.text)
            if not data:
                await interaction.edit_original_response(content="生成題目時發生錯誤，請稍後再試。")
                return
            quiz_questions = data[:questions]
            state = SocialState(interaction.user.id, quiz_questions)
            social_games[interaction.user.id] = state
            first = quiz_questions[0]
            embed = _create_question_embed(first, 1, state.total)
            view = SocialQuizView(state)
            await interaction.edit_original_response(content="", embed=embed, view=view)
        except json.JSONDecodeError as e:
            await interaction.edit_original_response(content=f"模型輸出非合法JSON：{e}")
        except Exception as e:
            await interaction.edit_original_response(content=f"產生題目時發生錯誤：{e}")


def register(bot: commands.Bot):
    bot.tree.add_command(Social())


