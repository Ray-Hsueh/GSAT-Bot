# GSAT 學測練習 Discord 機器人

使用 Python 與 Discord.py 開發的學測練習機器人，已模組化各科目結構。英文科整合 Google Gemini 2.5 Flash Lite 生成題目。

## 功能特色

- 🎯 基於學測6000字單字庫的練習
- 🤖 使用 Gemini AI 生成符合學測難度的題目
- ⏰ 詞彙：每題 3 分鐘；綜合：整份 5 分鐘超時機制
- 🎨 美觀的 Discord Embed 介面
- 📊 即時對答和詳細解析（綜合測驗於作答完畢後一次性公布）
- 🎮 互動式按鈕操作

## 安裝與啟動

### 1. 環境需求

- Python 3.8 或更高版本
- Discord Bot Token
- Google Gemini API Key

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 環境變數設定（.env）

創建 `.env` 檔案並設定以下變數：

```env
DISCORD_TOKEN=你的Discord機器人Token
GEMINI_API_KEY=你的Gemini API Key
```

### 4. 啟動主程式

```bash
python main.py
```

## 使用說明

### 指令列表（英文）

- `/english vocabulary [題數] [級別]` - 開始測驗
  - 題數：1-20題（預設5題）
  - 級別：1-6級（可選；未指定時將從所有級別隨機挑選單字）

- `/english comprehensive` - 開始綜合測驗，最後統一公布解答
  - 生成一篇含 5 個空格的短文
  - 作答期間逐題顯示選項但不公布正解
  - 全部作答完後一次性顯示：每題正誤、你的答案、正確答案、詳解

- `/help` - 顯示幫助資訊

### 使用範例

```
/vocabulary                     # 開始5題，從所有級別挑選單字
/vocabulary questions:10        # 開始10題，從所有級別挑選單字
/vocabulary questions:5 level:3 # 開始5題第3級測驗
/vocabulary questions:20 level:6 # 開始20題第6級測驗

/comprehensive                  # 開始綜合測驗（5空），最後統一公布解答
```

## 檔案結構與模組

```
GSAT-Bot/
├── main.py                # 主程式（初始化 bot，註冊科目模組）
├── english.py             # 英文科
├── chinese.py             # 國文科
├── subject_math.py        # 數學科
├── science.py             # 自然科
├── social.py              # 社會科
├── 學測6000字.csv        # 英文單字資料庫
├── requirements.txt       # Python 依賴
├── .env                   # 環境變數（需自行創建）
└── README.md              # 說明文件
```

在 `main.py` 中會自動註冊各模組的 `register(bot)`：

```python
import english
import chinese
import subject_math
import science
import social

def register_subjects():
    english.register(bot)
    chinese.register(bot)
    subject_math.register(bot)
    science.register(bot)
    social.register(bot)
```

## 功能詳解

### 單字選擇機制

- 支援按級別篩選單字（1-6級）
- 自動處理 `actor/actress` 格式的單字，隨機選擇其中一個
- 確保選中的單字不會重複出現在選項中

### AI 題目生成

- 使用 Gemini 2.5 Flash Lite 生成符合學測難度的題目
- 自動生成選項
- 提供詳解

### 超時機制

- 詞彙測驗：每題限制 3 分鐘作答時間
- 綜合測驗：整份測驗 5 分鐘；逾時自動結束
- 防止機器人資源被長期佔用

## 注意事項與提示

1. 確保 `.env` 已正確設定 `DISCORD_TOKEN` 與 `GEMINI_API_KEY`
2. 若出現 `module 'math' has no attribute 'register'`，請確認使用的是 `subject_math.py`（避免與內建 `math` 衝突）
3. Gemini API 有使用限制，請注意 API 配額
4. 建議在測試環境中先驗證功能正常

## 授權

本專案採用 MIT 授權條款。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！
