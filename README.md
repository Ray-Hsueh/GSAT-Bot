# 學測英文練習 Discord 機器人

這是一個使用 Python 和 Discord.py 開發的學測英文單字練習機器人，整合了 Google Gemini 2.5 Flash Lite API 來生成題目。

## 功能特色

- 🎯 基於學測6000字單字庫的練習
- 🤖 使用 Gemini AI 生成符合學測難度的題目
- ⏰ 3分鐘超時機制，防止測驗無限進行
- 🎨 美觀的 Discord Embed 介面
- 📊 即時成績統計和詳細解析
- 🎮 互動式按鈕操作

## 安裝說明

### 1. 環境需求

- Python 3.8 或更高版本
- Discord Bot Token
- Google Gemini API Key

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 環境變數設定

創建 `.env` 檔案並設定以下變數：

```env
DISCORD_TOKEN=你的Discord機器人Token
GEMINI_API_KEY=你的Gemini API Key
```

### 4. 運行機器人

```bash
python main.py
```

## 使用說明

### 指令列表

- `/start [題數] [級別]` - 開始測驗
  - 題數：1-20題（預設5題）
  - 級別：1-6級（可選，不指定則隨機選擇）
  
- `/stop` - 停止當前測驗

- `/help` - 顯示幫助資訊

### 使用範例

```
/start                    # 開始5題隨機級別測驗
/start questions:10       # 開始10題隨機級別測驗
/start questions:5 level:3 # 開始5題第3級測驗
/start questions:20 level:6 # 開始20題第6級測驗
```

## 檔案結構

```
GSAT-English-Practice-Bot/
├── main.py              # 主程式
├── requirements.txt     # Python依賴
├── 學測6000字.csv      # 單字資料庫
├── .env                 # 環境變數（需自行創建）
└── README.md           # 說明文件
```

## 功能詳解

### 單字選擇機制

- 支援按級別篩選單字（1-6級）
- 自動處理 `actor/actress` 格式的單字，隨機選擇其中一個
- 確保選中的單字不會重複出現在選項中

### AI 題目生成

- 使用 Gemini 2.5 Flash Lite 生成符合學測難度的題目
- 自動生成具有誘答力的選項
- 提供繁體中文詳解

### 超時機制

- 每題限制3分鐘作答時間
- 超時自動結束測驗
- 防止機器人資源被長期佔用

### 成績統計

- 即時計算正確率
- 提供等級評定（優秀/良好/及格/需要加強）
- 詳細的錯誤解析

## 技術架構

### 主要技術棧

- **Discord.py**: Discord API 客戶端
- **Pandas**: 資料處理和CSV讀取
- **Google Generative AI**: AI題目生成
- **Asyncio**: 異步程式設計

### 核心類別

- `GameState`: 管理用戶遊戲狀態
- `QuizView`: Discord UI 互動介面
- 各種 Embed 創建函數

## 注意事項

1. 確保機器人有足夠的權限在 Discord 伺服器中運行
2. Gemini API 有使用限制，請注意 API 配額
3. 建議在測試環境中先驗證功能正常

## 授權

本專案採用 MIT 授權條款。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！
