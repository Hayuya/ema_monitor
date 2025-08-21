#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - メインプログラム
CBP501の三相治験開始のニュースがあるかどうかのみを判定・報告
"""

import logging
import sys
from datetime import datetime
import os
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
        
        return {
            'discord_webhook': discord_webhook,
            'status_report_interval': int(os.getenv('STATUS_REPORT_INTERVAL', '4'))
        }
    except Exception as e:
        logger.error(f"環境変数の読み込みに失敗: {e}")
        sys.exit(1)

def load_execution_counter():
    """実行回数カウンターを読み込み"""
    try:
        if os.path.exists('execution_counter.txt'):
            with open('execution_counter.txt', 'r', encoding='utf-8') as f:
                return int(f.read().strip())
        return 0
    except Exception as e:
        logger.warning(f"実行回数カウンターの読み込みに失敗: {e}")
        return 0

def save_execution_counter(counter):
    """実行回数カウンターを保存"""
    try:
        with open('execution_counter.txt', 'w', encoding='utf-8') as f:
            f.write(str(counter))
        logger.debug(f"実行回数カウンター保存: {counter}")
    except Exception as e:
        logger.error(f"実行回数カウンターの保存に失敗: {e}")

def load_last_found_status():
    """前回のCBP501発見状況を読み込み"""
    try:
        if os.path.exists('cbp501_status.txt'):
            with open('cbp501_status.txt', 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "未発見"
    except Exception as e:
        logger.warning(f"前回ステータスの読み込みに失敗: {e}")
        return "未発見"

def save_cbp501_status(status):
    """CBP501発見状況を保存"""
    try:
        with open('cbp501_status.txt', 'w', encoding='utf-8') as f:
            f.write(status)
        logger.info(f"CBP501ステータス保存: {status}")
    except Exception as e:
        logger.error(f"CBP501ステータスの保存に失敗: {e}")

def main():
    """メイン処理"""
    logger.info("=== CBP501三相治験監視アプリ開始 ===")
    
    # 環境設定読み込み
    config = load_environment()
    
    # 実行回数カウンターを更新
    execution_counter = load_execution_counter() + 1
    save_execution_counter(execution_counter)
    
    # 前回のCBP501発見状況を読み込み
    last_status = load_last_found_status()
    logger.info(f"実行回数: {execution_counter}, 前回CBP501ステータス: {last_status}")
    
    # Discord通知インスタンスを作成
    notifier = CBP501Notifier(config['discord_webhook'])
    
    try:
        # CBP501情報をスクレイピング
        scraper = CBP501Scraper()
        logger.info("CBP501三相治験情報の検索を開始")
        
        # CBP501の三相治験情報を検索
        cbp501_found, cbp501_details = scraper.search_cbp501_phase3()
        
        current_status = "発見" if cbp501_found else "未発見"
        
        # ステータスが変化したか、定期報告時期かを判定
        status_changed = (current_status != last_status)
        should_report = (execution_counter % config['status_report_interval'] == 0)
        
        if cbp501_found:
            logger.info("🎉 CBP501三相治験情報を発見！")
            
            if status_changed:
                # 新規発見時の特別通知
                notifier.send_cbp501_found_notification(cbp501_details)
                logger.info("CBP501発見の緊急通知を送信しました")
            elif should_report:
                # 定期報告（発見継続中）
                notifier.send_status_report(True, cbp501_details, execution_counter)
                logger.info("定期報告を送信しました（CBP501発見継続中）")
            
        else:
            logger.info("CBP501三相治験情報は見つかりませんでした")
            
            if status_changed:
                # 発見状態から未発見に変化（稀なケース）
                notifier.send_cbp501_status_change(False, execution_counter)
                logger.info("CBP501状態変化通知を送信しました（発見→未発見）")
            elif should_report:
                # 定期報告（未発見継続中）
                notifier.send_status_report(False, None, execution_counter)
                logger.info("定期報告を送信しました（CBP501未発見継続中）")
        
        # 今回のステータスを保存
        save_cbp501_status(current_status)
        
        # ログに結果をまとめて出力
        logger.info(f"監視結果: CBP501三相治験 = {current_status}")
        logger.info(f"通知送信: {'あり' if (status_changed or should_report) else 'なし'}")
        
    except Exception as e:
        logger.error(f"メイン処理でエラーが発生: {e}")
        
        # エラー通知をDiscordに送信
        try:
            error_message = f"❌ **CBP501監視エラー** (実行回数: {execution_counter})\n\n"
            error_message += f"エラー内容: {str(e)}\n"
            error_message += f"⏰ 発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            error_message += f"🔄 次回実行: 15分後に自動復旧を試行"
            
            notifier.send_error_notification(error_message)
        except:
            pass
        
        sys.exit(1)
    
    logger.info("=== CBP501三相治験監視アプリ終了 ===")

if __name__ == "__main__":
    main()