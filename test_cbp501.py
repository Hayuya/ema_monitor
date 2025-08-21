#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - テストスクリプト
CBP501専用システムの各機能をテストする
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
    
    print(f"✅ STATUS_REPORT_INTERVAL: {os.getenv('STATUS_REPORT_INTERVAL', '4')}")
    
    return True

def test_cbp501_scraper():
    """CBP501スクレイピング機能のテスト"""
    print("\n=== CBP501スクレイピング機能テスト ===")
    
    try:
        from cbp501_scraper import CBP501Scraper
        
        scraper = CBP501Scraper()
        print("✅ CBP501Scraper初期化: 成功")
        
        # CBP501三相治験情報の検索テスト
        print("🔍 CBP501三相治験情報を検索中...")
        cbp501_found, cbp501_details = scraper.search_cbp501_phase3()
        
        if cbp501_found:
            print(f"🎉 CBP501三相治験情報を発見！ ({len(cbp501_details)}件)")
            for i, item in enumerate(cbp501_details, 1):
                print(f"   {i}. {item['title'][:80]}...")
                print(f"      信頼度: {item.get('confidence', 'unknown')}")
                print(f"      ソース: {item['source']}")
                if item.get('url'):
                    print(f"      URL: {item['url']}")
        else:
            if cbp501_details:
                print(f"⚠️ CBP501情報は見つかりましたが三相治験ではありません ({len(cbp501_details)}件)")
                for i, item in enumerate(cbp501_details, 1):
                    print(f"   {i}. {item['title'][:60]}...")
            else:
                print("ℹ️ CBP501に関する情報は現在見つかりませんでした")
        
        return True
        
    except Exception as e:
        print(f"❌ CBP501スクレイピングテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cbp501_notifier():
    """CBP501 Discord通知機能のテスト"""
    print("\n=== CBP501 Discord通知機能テスト ===")
    
    try:
        from cbp501_notifier import CBP501Notifier
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            print("❌ DISCORD_WEBHOOK_URL が設定されていません")
            return False
        
        notifier = CBP501Notifier(webhook_url)
        print("✅ CBP501Notifier初期化: 成功")
        
        # 接続テスト
        print("🔗 Discord接続テスト中...")
        success = notifier.test_connection()
        
        if success:
            print("✅ Discord接続テスト: 成功")
        else:
            print("❌ Discord接続テスト: 失敗")
            return False
        
        # テスト通知の送信
        print("📤 CBP501ステータス報告テスト中...")
        success = notifier.send_status_report(False, None, 1)
        
        if success:
            print("✅ CBP501ステータス報告テスト: 成功")
        else:
            print("❌ CBP501ステータス報告テスト: 失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ CBP501通知テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cbp501_full_workflow():
    """CBP501完全ワークフローのテスト"""
    print("\n=== CBP501完全ワークフローテスト ===")
    
    try:
        from cbp501_scraper import CBP501Scraper
        from cbp501_notifier import CBP501Notifier
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        scraper = CBP501Scraper()
        notifier = CBP501Notifier(webhook_url)
        
        # 実際のCBP501検索を実行
        print("🔍 実際のCBP501情報を検索中...")
        cbp501_found, cbp501_details = scraper.search_cbp501_phase3()
        
        print(f"検索結果: CBP501三相治験 = {'発見' if cbp501_found else '未発見'}")
        
        if cbp501_found:
            # CBP501発見時のテスト通知
            print("📤 CBP501発見通知（テスト）送信中...")
            # テスト用にタイトルを変更
            test_details = []
            for detail in cbp501_details:
                test_detail = detail.copy()
                test_detail['title'] = f"🧪 [テスト] {detail['title']}"
                test_details.append(test_detail)
            
            success = notifier.send_cbp501_found_notification(test_details)
            
            if success:
                print("✅ CBP501発見通知テスト: 成功")
            else:
                print("❌ CBP501発見通知テスト: 失敗")
                return False
        else:
            # CBP501未発見時のステータス報告
            print("📤 CBP501未発見ステータス報告（テスト）送信中...")
            success = notifier.send_status_report(False, cbp501_details, 999)
            
            if success:
                print("✅ CBP501未発見ステータス報告テスト: 成功")
            else:
                print("❌ CBP501未発見ステータス報告テスト: 失敗")
                return False
        
        return True
            
    except Exception as e:
        print(f"❌ CBP501完全ワークフローテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト関数"""
    print("🧬 CBP501三相治験監視システム テストスイート")
    print("=" * 60)
    
    # 各テストを実行
    tests = [
        ("環境設定", test_environment),
        ("CBP501スクレイピング機能", test_cbp501_scraper),
        ("CBP501 Discord通知機能", test_cbp501_notifier),
        ("CBP501完全ワークフロー", test_cbp501_full_workflow)
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
    print("\n" + "=" * 60)
    print("📊 CBP501テスト結果まとめ")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("🧬 CBP501監視システムは正常に動作します。")
        print("\n📋 次のステップ:")
        print("1. GitHub Actions設定ファイルをリポジトリに追加")
        print("2. DISCORD_WEBHOOK_URLをGitHub Secretsに設定")
        print("3. 15分間隔での自動監視開始")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました。設定を確認してください。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)