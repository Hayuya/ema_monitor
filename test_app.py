#!/usr/bin/env python3
"""
EMA承認監視アプリケーション - テストスクリプト
アプリケーションの各機能をテストする
"""

import os
import sys
import logging
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment():
    """環境設定のテスト"""
    print("=== 環境設定テスト ===")
    
    # .envファイルの読み込み
    load_dotenv()
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if webhook_url:
        print("✅ DISCORD_WEBHOOK_URL: 設定済み")
        # URLの形式をチェック
        if webhook_url.startswith('https://discord.com/api/webhooks/'):
            print("✅ Webhook URL形式: 正常")
        else:
            print("❌ Webhook URL形式: 無効")
            return False
    else:
        print("❌ DISCORD_WEBHOOK_URL: 未設定")
        return False
    
    print(f"✅ CHECK_INTERVAL_HOURS: {os.getenv('CHECK_INTERVAL_HOURS', '1')}")
    print(f"✅ MAX_NEWS_ITEMS: {os.getenv('MAX_NEWS_ITEMS', '10')}")
    
    return True

def test_scraper():
    """スクレイピング機能のテスト"""
    print("\n=== スクレイピング機能テスト ===")
    
    try:
        from scraper import EMAScraper
        
        scraper = EMAScraper()
        print("✅ EMAScraper初期化: 成功")
        
        # 最新ニュースの取得テスト
        print("🔍 最新ニュースを取得中...")
        news_items = scraper.get_latest_news(max_items=3)
        
        if news_items:
            print(f"✅ ニュース取得: 成功 ({len(news_items)}件)")
            for i, item in enumerate(news_items, 1):
                print(f"   {i}. {item['title'][:60]}...")
                print(f"      承認関連: {'はい' if item['is_approval_related'] else 'いいえ'}")
        else:
            print("❌ ニュース取得: 失敗")
            return False
        
        # CHMPハイライトの取得テスト
        print("\n🔍 CHMPハイライトを取得中...")
        chmp_items = scraper.get_chmp_highlights()
        
        if chmp_items:
            print(f"✅ CHMPハイライト取得: 成功 ({len(chmp_items)}件)")
            for i, item in enumerate(chmp_items, 1):
                print(f"   {i}. {item['title'][:60]}...")
        else:
            print("⚠️ CHMPハイライト取得: 0件（エラーではありません）")
        
        return True
        
    except Exception as e:
        print(f"❌ スクレイピングテスト失敗: {e}")
        return False

def test_notifier():
    """Discord通知機能のテスト"""
    print("\n=== Discord通知機能テスト ===")
    
    try:
        from notifier import DiscordNotifier
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            print("❌ DISCORD_WEBHOOK_URL が設定されていません")
            return False
        
        notifier = DiscordNotifier(webhook_url)
        print("✅ DiscordNotifier初期化: 成功")
        
        # 接続テスト
        print("🔗 Discord接続テスト中...")
        success = notifier.test_connection()
        
        if success:
            print("✅ Discord接続テスト: 成功")
        else:
            print("❌ Discord接続テスト: 失敗")
            return False
        
        # テスト通知の送信
        print("📤 テスト通知送信中...")
        test_news_item = {
            'id': 'test_001',
            'title': '🧪 EMA監視アプリ テスト通知',
            'link': 'https://www.ema.europa.eu/',
            'date': '2025年8月17日',
            'description': 'これはアプリケーションのテスト通知です。正常に動作しています。',
            'is_approval_related': True
        }
        
        success = notifier.send_approval_notification(test_news_item)
        
        if success:
            print("✅ テスト通知送信: 成功")
        else:
            print("❌ テスト通知送信: 失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 通知テスト失敗: {e}")
        return False

def test_full_workflow():
    """完全なワークフローのテスト"""
    print("\n=== 完全ワークフローテスト ===")
    
    try:
        from scraper import EMAScraper
        from notifier import DiscordNotifier
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        scraper = EMAScraper()
        notifier = DiscordNotifier(webhook_url)
        
        # 実際のニュースを取得
        print("🔍 実際のニュースを取得中...")
        news_items = scraper.get_latest_news(max_items=1)
        
        if news_items:
            item = news_items[0]
            print(f"✅ 取得したニュース: {item['title'][:50]}...")
            
            # 実際の通知を送信（テスト用にタイトルを変更）
            test_item = item.copy()
            test_item['title'] = f"🧪 [テスト] {item['title']}"
            test_item['description'] = f"[テスト送信] {item.get('description', '')}"
            
            print("📤 実際のニュースでテスト通知送信中...")
            success = notifier.send_approval_notification(test_item)
            
            if success:
                print("✅ 完全ワークフローテスト: 成功")
                return True
            else:
                print("❌ 完全ワークフローテスト: 通知送信失敗")
                return False
        else:
            print("❌ 完全ワークフローテスト: ニュース取得失敗")
            return False
            
    except Exception as e:
        print(f"❌ 完全ワークフローテスト失敗: {e}")
        return False

def main():
    """メインテスト関数"""
    print("🧪 EMA承認監視アプリケーション テストスイート")
    print("=" * 50)
    
    # 各テストを実行
    tests = [
        ("環境設定", test_environment),
        ("スクレイピング機能", test_scraper),
        ("Discord通知機能", test_notifier),
        ("完全ワークフロー", test_full_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}テストでエラー: {e}")
            results.append((test_name, False))
    
    # 結果まとめ
    print("\n" + "=" * 50)
    print("📊 テスト結果まとめ")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！アプリケーションは正常に動作します。")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)