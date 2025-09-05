#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - スクレイピング処理
EMA（欧州医薬品庁）のウェブサイトからCBP501の三相治験情報を取得
"""

import logging
import time
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class CBP501Scraper:
    """CBP501治験情報スクレイパークラス"""

    def __init__(self):
        """初期化"""
        self.base_urls = [
            'https://www.ema.europa.eu/en/news',
            'https://www.ema.europa.eu/en/human-regulatory/research-and-development/clinical-trials-human-medicines'
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_request(self, url, max_retries=3):
        """リクエストを送信"""
        logger.info(f"リクエスト送信: {url} (試行 1/{max_retries})")
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"リクエスト失敗 (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

    def search_cbp501_phase3(self):
        """CBP501の三相治験情報を検索"""
        logger.info("CBP501三相治験情報の検索を開始")
        found_items = []

        for url in self.base_urls:
            logger.info(f"検索対象: {url}")
            response = self._get_request(url)

            if response:
                try:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # 治験情報が含まれる可能性のある要素を広く検索
                    search_text = soup.get_text()

                    if "CBP501" in search_text and "Phase III" in search_text:
                        logger.info(f"{url}でCBP501の三相治験情報が見つかりました")
                        # 詳細情報を抽出（サンプル）
                        title = soup.title.string
                        content = soup.find('meta', attrs={'name': 'description'})['content']
                        
                        found_items.append({
                            'source': url,
                            'title': title,
                            'content': content,
                            'url': response.url,
                            'confidence': 'high',
                            'phase3_keywords': ['Phase III'],
                            'start_keywords': []
                        })
                except Exception as e:
                    logger.error(f"{url}の解析中にエラー: {e}")
            else:
                logger.warning(f"検索エラー ({url}): リクエストに失敗しました")

        if found_items:
            logger.info(f"{len(found_items)}件のCBP501三相治験関連情報が見つかりました")
            return True, found_items
        else:
            logger.info("CBP501に関する情報は見つかりませんでした")
            return False, []