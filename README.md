# EMA承認監視アプリケーション

欧州医薬品庁（EMA）の新薬承認発表を自動監視し、Discordに通知するアプリケーションです。

## 🎯 主な機能

- **自動監視**: EMAの公式サイトを1時間ごとに監視
- **Discord通知**: 新しい承認情報をDiscordチャンネルに自動投稿
- **承認特化**: 新薬承認関連のニュースを優先的に検出・通知
- **完全自動化**: GitHub Actionsによる24時間自動運用

## 📋 監視対象

- EMAニュースページ: https://www.ema.europa.eu/en/news
- CHMP会議ハイライト（新薬承認の詳細情報）
- プレスリリース・承認発表

## 🚀 セットアップ手順

### 1. リポジトリの作成とクローン

```bash
# GitHubでリポジトリを作成後
git clone https://github.com/your-username/ema-monitor.git
cd ema-monitor
```

### 2. Discord Webhookの設定

1. Discordサーバーで通知を受け取りたいチャンネルを開く
2. チャンネル設定 → 連携サービス → ウェブフック → 新しいウェブフック
3. ウェブフック名を「EMA Monitor」に設定
4. ウェブフックURLをコピー

### 3. 環境変数の設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してWebhook URLを設定
nano .env
```

`.env`ファイルの内容：
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
CHECK_INTERVAL_HOURS=1
MAX_NEWS_ITEMS=10
```

### 4. GitHub Secretsの設定

1. GitHubリポジトリ → Settings → Secrets and variables → Actions
2. 「New repository secret」をクリック
3. Name: `DISCORD_WEBHOOK_URL`
4. Secret: Discord Webhook URLを貼り付け

### 5. ローカルでのテスト実行

```bash
# Python仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# テスト実行
python main.py
```

## ⚙️ GitHub Actionsによる自動実行

リポジトリにコードをプッシュすると、GitHub Actionsが自動的に：

- **毎時0分に実行**（UTC時間）
- **新しい承認情報を検出**
- **Discordに通知を送信**

### 手動実行

GitHub リポジトリ → Actions → EMA承認監視アプリ → Run workflow

## 📁 プロジェクト構造

```
ema_monitor/
├── .github/
│   └── workflows/
│       └── main.yml          # GitHub Actions設定
├── .env.example             # 環境変数テンプレート
├── .gitignore              # Git除外設定
├── main.py                 # メインプログラム
├── scraper.py              # EMAサイトスクレイピング
├── notifier.py             # Discord通知機能
├── requirements.txt        # Python依存関係
└── README.md              # このファイル
```

## 🔧 主な設定オプション

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 必須 |
| `CHECK_INTERVAL_HOURS` | チェック間隔（時間） | 1 |
| `MAX_NEWS_ITEMS` | 取得する最大ニュース数 | 10 |

### GitHub Actions スケジュール

`.github/workflows/main.yml`でcron設定を変更可能：

```yaml
on:
  schedule:
    - cron: '0 * * * *'  # 毎時0分（UTC）
```

## 📊 通知の種類

### 🎯 新薬承認通知（緑色）
- 新薬の承認推奨
- CHMP会議の決定事項
- マーケティング認可

### 📰 一般ニュース通知（青色）
- その他のEMAニュース
- 安全性情報
- ガイドライン更新

### ⚠️ エラー通知（赤色）
- アプリケーションエラー
- 接続問題
- スクレイピング失敗

## 🐛 トラブルシューティング

### よくある問題

**1. 通知が届かない**
- Discord Webhook URLが正しく設定されているか確認
- GitHub Secretsの設定を確認
- Actions タブでエラーログを確認

**2. 重複通知が送信される**
- `last_check.txt`ファイルが正常に作成されているか確認
- GitHub Actionsのキャッシュ設定を確認

**3. スクレイピングエラー**
- EMAサイトの構造変更の可能性
- ネットワーク接続の確認
- User-Agent設定の確認

### ログの確認

```bash
# ローカル実行時
cat ema_monitor.log

# GitHub Actions
# Actions → 実行履歴 → ログを確認
```

## 🔒 セキュリティ

- **機密情報**: Discord Webhook URLは`.env`ファイルで管理
- **GitHub Secrets**: 本番環境ではGitHub Secretsを使用
- **除外設定**: `.gitignore`で機密ファイルを除外

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します：

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ⚡ 更新履歴

- **v1.0.0**: 初回リリース
  - EMAニュース監視機能
  - Discord通知機能  
  - GitHub Actions自動実行

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページでお知らせください。

---

**注意**: このアプリケーションは教育・情報提供目的で開発されています。EMAの公式情報は必ず原典で確認してください。