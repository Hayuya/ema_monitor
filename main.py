#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - メインプログラム
CBP501の三相治験開始のニュースがあるかどうかのみを判定・報告
"""

import logging
import sys
from datetime import datetime
import os
import pytz
from cbp501_scraper import CBP501Scraper
from cbp501_notifier import CBP501Notifier

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cbp501_monitor.log')
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
        
        return {'discord_webhook': discord_webhook}
    except Exception as e:
        logger.error(f"環境変数の読み込みに失敗: {e}")
        sys.exit(1)

def load_last_run_data(file_path):
    """最終実行データを読み込む"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    except Exception as e:
        logger.warning(f"{file_path} の読み込みに失敗: {e}")
        return None

def save_run_data(file_path, data):
    """実行データを保存"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(data))
    except Exception as e:
        logger.error(f"{file_path} の保存に失敗: {e}")

def main():
    """メイン処理"""
    logger.info("=== CBP501三相治験監視アプリ開始 ===")
    
    config = load_environment()
    notifier = CBP501Notifier(config['discord_webhook'])
    
    # 実行回数を読み込んで1加算
    try:
        execution_count = int(load_last_run_data('execution_counter.txt') or 0) + 1
    except ValueError:
        execution_count = 1
    
    # 初回実行の場合、ステータスレポートを送信
    if execution_count == 1:
        logger.info("初回実行です。")
        # 引数を揃えて初回レポートを送信
        notifier.send_status_report(False, [], 0)

    try:
        # 治験情報のスクレイピング
        scraper = CBP501Scraper()
        logger.info("CBP501三相治験情報の検索を開始")
        cbp501_found, cbp501_details = scraper.search_cbp501_phase3()
        
        current_status = "発見" if cbp501_found else "未発見"
        last_status = load_last_run_data('cbp501_status.txt') or "未発見"
        
        # 治験情報が新たに見つかった場合に通知
        if cbp501_found and current_status != last_status:
            logger.info("🎉 CBP501三相治験情報を新規発見！")
            notifier.send_cbp501_found_notification(cbp501_details)
        
        # 状態を保存
        save_run_data('cbp501_status.txt', current_status)

        # 日本時間の21時台に生存確認を1日1回送信
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        today_str = now_jst.strftime('%Y-%m-%d')
        last_survival_check_date = load_last_run_data('last_survival_check.txt')

        if now_jst.hour == 21 and last_survival_check_date != today_str:
            logger.info("生存確認通知を送信します。")
            # 修正箇所：引数を正しく渡す
            notifier.send_status_report(cbp501_found, cbp501_details, execution_count)
            save_run_data('last_survival_check.txt', today_str)

    except Exception as e:
        logger.error(f"メイン処理でエラーが発生: {e}", exc_info=True)
        try:
            error_message = f"❌ **CBP501監視エラー**\n\n"
            error_message += f"エラー内容: `{str(e)}`\n"
            error_message += f"⏰ 発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            notifier.send_error_notification(error_message)
        except Exception as notify_error:
            logger.error(f"エラー通知の送信に失敗: {notify_error}")
        sys.exit(1)
    finally:
        # 実行回数を保存
        save_run_data('execution_counter.txt', execution_count)
    
    logger.info("=== CBP501三相治験監視アプリ終了 ===")

if __name__ == "__main__":
    main()