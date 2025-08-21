#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - Discord通知処理
CBP501三相治験情報の発見・未発見をDiscordに通知
"""

import requests
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class CBP501Notifier:
    """CBP501専用Discord通知クラス"""
    
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CBP501-Monitor-Bot/1.0'
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
    
    def send_cbp501_found_notification(self, cbp501_details):
        """CBP501三相治験発見時の緊急通知"""
        try:
            # 最も信頼度の高いアイテムを選択
            best_item = max(cbp501_details, key=lambda x: x.get('confidence', 'low') == 'high')
            
            embed = {
                "title": "🚨 CBP501三相治験情報を発見！",
                "description": f"**{best_item['title']}**\n\n{best_item['content'][:300]}{'...' if len(best_item['content']) > 300 else ''}",
                "url": best_item['url'] if best_item['url'] else best_item['source'],
                "color": 0xFF0000,  # 赤色（緊急）
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "CBP501 Phase III Trial Monitor",
                    "icon_url": "https://www.ema.europa.eu/sites/default/files/ema_logo.png"
                },
                "fields": [
                    {
                        "name": "🎯 薬剤名",
                        "value": "CBP501",
                        "inline": True
                    },
                    {
                        "name": "📊 治験段階",
                        "value": "Phase III（三相）",
                        "inline": True
                    },
                    {
                        "name": "🔍 信頼度",
                        "value": best_item.get('confidence', 'medium').title(),
                        "inline": True
                    },
                    {
                        "name": "📅 発見時刻",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S JST'),
                        "inline": True
                    },
                    {
                        "name": "📍 情報源",
                        "value": best_item['source'],
                        "inline": True
                    },
                    {
                        "name": "📝 発見詳細",
                        "value": f"合計 {len(cbp501_details)} 件の関連情報を発見",
                        "inline": True
                    }
                ]
            }
            
            # キーワード情報を追加
            if best_item.get('phase3_keywords') or best_item.get('start_keywords'):
                keywords = []
                if best_item.get('phase3_keywords'):
                    keywords.extend([f"Phase3: {kw}" for kw in best_item['phase3_keywords'][:3]])
                if best_item.get('start_keywords'):
                    keywords.extend([f"Start: {kw}" for kw in best_item['start_keywords'][:3]])
                
                embed["fields"].append({
                    "name": "🔑 検出キーワード",
                    "value": ", ".join(keywords[:5]),
                    "inline": False
                })
            
            payload = {
                "content": "@everyone 🚨 **CBP501三相治験情報発見！** 🚨",
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"CBP501発見通知の構築に失敗: {e}")
            return False
    
    def send_status_report(self, cbp501_found, cbp501_details, execution_count):
        """定期ステータス報告"""
        try:
            if cbp501_found:
                # 発見継続中の報告
                title = "📊 CBP501監視 定期報告（発見継続中）"
                color = 0x00FF00  # 緑色
                description = "🎉 CBP501三相治験情報が引き続き確認できています。"
                
                fields = [
                    {
                        "name": "🎯 監視対象",
                        "value": "CBP501三相治験開始情報",
                        "inline": True
                    },
                    {
                        "name": "📊 現在の状況",
                        "value": "**発見中** ✅",
                        "inline": True
                    },
                    {
                        "name": "📝 発見件数",
                        "value": f"{len(cbp501_details)}件",
                        "inline": True
                    }
                ]
            else:
                # 未発見継続中の報告
                title = "📊 CBP501監視 定期報告"
                color = 0x808080  # グレー色
                description = "🔍 CBP501三相治験情報を継続監視中です。現在のところ該当情報は見つかっていません。"
                
                fields = [
                    {
                        "name": "🎯 監視対象",
                        "value": "CBP501三相治験開始情報",
                        "inline": True
                    },
                    {
                        "name": "📊 現在の状況",
                        "value": "監視中（未発見）",
                        "inline": True
                    },
                    {
                        "name": "🔄 監視継続",
                        "value": "15分ごとに自動チェック",
                        "inline": True
                    }
                ]
            
            # 共通フィールドを追加
            fields.extend([
                {
                    "name": "⏰ 報告時刻",
                    "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S JST'),
                    "inline": True
                },
                {
                    "name": "🔢 実行回数",
                    "value": f"{execution_count}回目",
                    "inline": True
                },
                {
                    "name": "📡 次回チェック",
                    "value": "15分後",
                    "inline": True
                }
            ])
            
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "CBP501 Monitoring System"
                },
                "fields": fields
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"ステータス報告の構築に失敗: {e}")
            return False
    
    def send_cbp501_status_change(self, now_found, execution_count):
        """CBP501情報の状態変化通知"""
        try:
            if now_found:
                title = "🎉 CBP501情報の状態変化"
                description = "CBP501三相治験情報が新たに発見されました！"
                color = 0x00FF00
            else:
                title = "⚠️ CBP501情報の状態変化"
                description = "以前発見されていたCBP501情報が確認できなくなりました。"
                color = 0xFFA500
            
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "CBP501 Status Change Alert"
                },
                "fields": [
                    {
                        "name": "🔄 状態変化",
                        "value": f"未発見 → 発見" if now_found else "発見 → 未発見",
                        "inline": True
                    },
                    {
                        "name": "🔢 実行回数",
                        "value": f"{execution_count}回目",
                        "inline": True
                    },
                    {
                        "name": "⏰ 変化検出時刻",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S JST'),
                        "inline": True
                    }
                ]
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"状態変化通知の構築に失敗: {e}")
            return False
    
    def send_error_notification(self, error_message):
        """エラー通知を送信"""
        try:
            embed = {
                "title": "⚠️ CBP501監視システムエラー",
                "description": error_message,
                "color": 0xFF0000,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "CBP501 Monitor - Error Alert"
                }
            }
            
            payload = {
                "content": "@here CBP501監視システムでエラーが発生しました",
                "embeds": [embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"エラー通知の送信に失敗: {e}")
            return False
    
    def test_connection(self):
        """Discord接続テスト"""
        try:
            test_embed = {
                "title": "🧪 CBP501監視システム 接続テスト",
                "description": "CBP501三相治験監視システムが正常に動作しています。",
                "color": 0x00FF00,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "CBP501 Monitor - Connection Test"
                }
            }
            
            payload = {
                "content": "CBP501監視システムが正常に動作しています ✅",
                "embeds": [test_embed]
            }
            
            return self._send_webhook(payload)
        
        except Exception as e:
            logger.error(f"接続テストに失敗: {e}")
            return False