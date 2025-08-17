#!/usr/bin/env python3
"""
EMA承認監視アプリケーション - メインプログラム
EMAの新薬承認発表を監視し、Discordへ通知するアプリケーション
"""

import logging
import sys
from datetime import datetime
import os
from scraper import EMAScraper
from notifier import DiscordNotifier

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ema_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

def load_environment():
    """環境変数の読み込み"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        if not discord_webhook:
            raise ValueError("DISCORD_WEBHOOK_URL環境変数が設定されていません")
        
        return {
            'discord_webhook': discord_webhook,
            'check_interval_hours': int(os.getenv('CHECK_INTERVAL_HOURS', '1')),
            'max_news_items': int(os.getenv('MAX_NEWS_ITEMS', '10'))
        }
    except Exception as e:
        logger.error(f"環境変数の読み込みに失敗: {e}")
        sys.exit(1)

def load_last_check_data():
    """前回チェック時のデータを読み込み"""
    try:
        if os.path.exists('last_check.txt'):
            with open('last_check.txt', 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.warning(f"前回チェックデータの読み込みに失敗: {e}")
        return None

def save_last_check_data(data):
    """今回のチェックデータを保存"""
    try:
        with open('last_check.txt', 'w', encoding='utf-8') as f:
            f.write(data)
        logger.info("チェックデータを保存しました")
    except Exception as e:
        logger.error(f"チェックデータの保存に失敗: {e}")

def main():
    """メイン処理"""
    logger.info("=== EMA承認監視アプリケーション開始 ===")
    
    # 環境設定読み込み
    config = load_environment()
    logger.info(f"設定読み込み完了: {config}")
    
    # 前回チェック時のデータを読み込み
    last_check_data = load_last_check_data()
    logger.info(f"前回チェック時データ: {last_check_data}")
    
    try:
        # EMAサイトをスクレイピング
        scraper = EMAScraper()
        logger.info("EMAサイトのスクレイピングを開始")
        
        # 最新ニュースを取得
        news_items = scraper.get_latest_news(max_items=config['max_news_items'])
        
        if not news_items:
            logger.warning("ニュース項目が見つかりませんでした")
            return
        
        # 新しいニュースがあるかチェック
        latest_news_id = news_items[0]['id']
        
        if last_check_data and latest_news_id == last_check_data:
            logger.info("新しいニュースはありません")
            return
        
        # 新しいニュースをフィルタリング
        if last_check_data:
            # 前回チェック以降の新しいニュースのみを抽出
            new_items = []
            for item in news_items:
                if item['id'] == last_check_data:
                    break
                new_items.append(item)
        else:
            # 初回実行時は最新の1件のみを通知
            new_items = news_items[:1]
        
        if new_items:
            logger.info(f"{len(new_items)}件の新しいニュースを発見")
            
            # Discord通知
            notifier = DiscordNotifier(config['discord_webhook'])
            
            for item in reversed(new_items):  # 古い順に通知
                try:
                    success = notifier.send_approval_notification(item)
                    if success:
                        logger.info(f"通知送信成功: {item['title'][:50]}...")
                    else:
                        logger.error(f"通知送信失敗: {item['title'][:50]}...")
                except Exception as e:
                    logger.error(f"通知送信中にエラー: {e}")
        
        # 今回のチェック結果を保存
        save_last_check_data(latest_news_id)
        
    except Exception as e:
        logger.error(f"メイン処理でエラーが発生: {e}")
        
        # エラー通知をDiscordに送信
        try:
            notifier = DiscordNotifier(config['discord_webhook'])
            notifier.send_error_notification(str(e))
        except:
            pass
        
        sys.exit(1)
    
    logger.info("=== EMA承認監視アプリケーション終了 ===")

if __name__ == "__main__":
    main()