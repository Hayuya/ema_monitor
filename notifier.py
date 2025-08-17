#!/usr/bin/env python3
"""
EMA承認監視アプリケーション - Discord通知処理
新薬承認情報をDiscordに通知する
"""

import requests
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscordNotifier:
    """Discord通知クラス"""
    
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EMA-Monitor-Bot/1.0'
        })
    
    def _send_webhook(self, payload, max_retries=3):
        """Discord Webhookにメッセージを送信"""
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 204:
                    return True
                elif response.status_code == 429:
                    # レート制限の場合は少し待つ
                    logger.warning("レート制限に達しました。5秒待機します。")
                    time.sleep(5)
                    continue
                else:
                    logger.error(f"Discord送信エラー: {response.status_code} - {response.text}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Discord送信リクエストエラー (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return False
        
        return False
    
    def send_approval_notification(self, news_item):
        """新薬承認通知を送信"""
        try:
            # 承認関連かどうかで色を変更
            color = 0x00FF00 if news_item['is_approval_related'] else 0x0099FF
            
            # タイトルから重要な情報を抽出
            title = news_item['title']
            description = news_item.get('description', '')
            
            # Embedメッセージを構築
            embed = {
                "title": title,
                "description": description if description else "詳細は以下のリンクをご確認ください。",
                "url": news_item['link'],
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "EMA (European Medicines Agency)",
                    "icon_url": "https://www.ema.europa.eu/sites/default/files/ema_logo.png"
                },
                "fields": []
            }
            
            # 日付情報があれば追加
            if news_item.get('date'):
                embed["fields"].append({
                    "name": "📅 発表日",
                    "value": news_item['date'],
                    "inline": True
                })
            
            # 承認関連の場合は特別なマークを追加
            if news_item['is_approval_related']:
                embed["fields"].append({
                    "name": "🎯 種別",
                    "value": "新薬承認関連",
                    "inline": True
                })
            
            # キーワード抽出
            keywords = self._extract_keywords(title + " " + description)
            if keywords:
                embed["fields"].append({
                    "name": "🔍 キーワード",
                    "value": ", ".join(keywords[:5]),  # 最大5個まで
                    "inline": False
                })
            
            # メッセージペイロード
            payload = {
                "embeds": [embed]
            }
            
            # 承認関連の場合は@everyoneを追加
            if news_item['is_approval_related']:
                payload["content"] = "🚨 **新薬承認情報** 🚨"
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"承認通知の構築に失敗: {e}")
            return False
    
    def send_error_notification(self, error_message):
        """エラー通知を送信"""
        try:
            embed = {
                "title": "⚠️ EMA監視アプリエラー",
                "description": f"アプリケーションでエラーが発生しました:\n```{error_message}```",
                "color": 0xFF0000,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "EMA Monitor App - Error Alert"
                }
            }
            
            payload = {
                "content": "@here エラーが発生しました",
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"エラー通知の送信に失敗: {e}")
            return False
    
    def send_status_notification(self, status_message):
        """ステータス通知を送信"""
        try:
            embed = {
                "title": "📊 EMA監視アプリ ステータス",
                "description": status_message,
                "color": 0x808080,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "EMA Monitor App - Status Update"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"ステータス通知の送信に失敗: {e}")
            return False
    
    def _extract_keywords(self, text):
        """テキストから重要なキーワードを抽出"""
        try:
            text_lower = text.lower()
            
            # 医薬品関連キーワード
            drug_keywords = [
                'vaccine', 'treatment', 'therapy', 'medicine', 'drug',
                'cancer', 'oncology', 'diabetes', 'cardiovascular',
                'antibiotic', 'antiviral', 'biosimilar', 'generic'
            ]
            
            # 承認関連キーワード
            approval_keywords = [
                'approved', 'authorisation', 'recommendation', 'chmp',
                'positive opinion', 'marketing authorisation', 'conditional'
            ]
            
            # 企業名キーワード
            company_keywords = [
                'pfizer', 'roche', 'novartis', 'gsk', 'astrazeneca',
                'merck', 'sanofi', 'johnson', 'bayer', 'takeda'
            ]
            
            all_keywords = drug_keywords + approval_keywords + company_keywords
            
            found_keywords = []
            for keyword in all_keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword.title())
            
            return list(set(found_keywords))  # 重複除去
        
        except Exception as e:
            logger.warning(f"キーワード抽出に失敗: {e}")
            return []
    
    def test_connection(self):
        """Discord接続テスト"""
        try:
            test_embed = {
                "title": "🧪 EMA監視アプリ 接続テスト",
                "description": "Discord通知が正常に動作しています。",
                "color": 0x00FF00,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "EMA Monitor App - Connection Test"
                }
            }
            
            payload = {
                "content": "EMA監視アプリが正常に動作しています ✅",
                "embeds": [test_embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"接続テストに失敗: {e}")
            return False