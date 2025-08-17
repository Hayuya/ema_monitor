#!/usr/bin/env python3
"""
EMA承認監視アプリケーション - スクレイピング処理
EMAの公式サイトから新薬承認情報を取得する
"""

import requests
import logging
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class EMAScraper:
    """EMAサイトのスクレイピングクラス"""
    
    def __init__(self):
        self.base_url = "https://www.ema.europa.eu"
        self.news_url = f"{self.base_url}/en/news"
        self.session = requests.Session()
        
        # User-Agentを設定
        self.session.headers.update({
            'User-Agent': 'EMA-Monitor-Bot/1.0 (Educational Purpose)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _make_request(self, url, max_retries=3):
        """HTTPリクエストを実行（リトライ機能付き）"""
        for attempt in range(max_retries):
            try:
                logger.info(f"リクエスト送信: {url} (試行 {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"リクエスト失敗 (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
                else:
                    raise
    
    def _extract_news_items(self, soup):
        """ニュース項目を抽出"""
        news_items = []
        
        try:
            # EMAのニュースページの構造に基づいて抽出
            # ニュース項目のコンテナを検索
            news_containers = soup.find_all(['article', 'div'], class_=re.compile(r'(news|item|card|listing)', re.I))
            
            if not news_containers:
                # 別のセレクタを試行
                news_containers = soup.find_all('div', class_=re.compile(r'view-content'))
                if news_containers:
                    news_containers = news_containers[0].find_all(['div', 'article'], recursive=True)
            
            logger.info(f"ニュースコンテナ数: {len(news_containers)}")
            
            for idx, container in enumerate(news_containers[:20]):  # 最大20件まで処理
                try:
                    item = self._parse_news_item(container, idx)
                    if item:
                        news_items.append(item)
                except Exception as e:
                    logger.warning(f"ニュース項目の解析に失敗 (項目 {idx}): {e}")
                    continue
        
        except Exception as e:
            logger.error(f"ニュース項目の抽出に失敗: {e}")
        
        return news_items
    
    def _parse_news_item(self, container, idx):
        """個別のニュース項目を解析"""
        try:
            # タイトルの抽出
            title_element = container.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|heading'))
            if not title_element:
                # リンクからタイトルを抽出
                link_element = container.find('a')
                if link_element:
                    title_element = link_element
            
            if not title_element:
                return None
            
            title = title_element.get_text(strip=True)
            
            # リンクの抽出
            link_element = title_element if title_element.name == 'a' else container.find('a')
            if link_element and link_element.get('href'):
                link = urljoin(self.base_url, link_element['href'])
            else:
                link = self.news_url
            
            # 日付の抽出
            date_element = container.find(['time', 'span', 'div'], class_=re.compile(r'date|time'))
            date_text = ""
            if date_element:
                date_text = date_element.get_text(strip=True)
            
            # 説明文の抽出
            description_element = container.find(['p', 'div'], class_=re.compile(r'summary|description|excerpt'))
            description = ""
            if description_element:
                description = description_element.get_text(strip=True)[:200] + "..."
            
            # 承認関連キーワードのチェック
            content_text = title.lower() + " " + description.lower()
            approval_keywords = [
                'recommended for approval', 'positive opinion', 'marketing authorisation',
                'new medicine', 'chmp', 'committee for medicinal products',
                'approved', 'authorisation', 'recommendation'
            ]
            
            is_approval_related = any(keyword in content_text for keyword in approval_keywords)
            
            # ユニークIDの生成
            item_id = f"{idx}_{hash(title + link)}"
            
            return {
                'id': item_id,
                'title': title,
                'link': link,
                'date': date_text,
                'description': description,
                'is_approval_related': is_approval_related
            }
        
        except Exception as e:
            logger.warning(f"ニュース項目の解析エラー: {e}")
            return None
    
    def get_latest_news(self, max_items=10):
        """最新ニュースを取得"""
        try:
            # メインニュースページを取得
            response = self._make_request(self.news_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info("ニュースページの解析を開始")
            
            # ニュース項目を抽出
            news_items = self._extract_news_items(soup)
            
            # 承認関連のニュースを優先してフィルタリング
            approval_news = [item for item in news_items if item['is_approval_related']]
            other_news = [item for item in news_items if not item['is_approval_related']]
            
            # 承認関連ニュースを優先し、残りを追加
            filtered_news = approval_news + other_news
            filtered_news = filtered_news[:max_items]
            
            logger.info(f"取得完了: 全{len(news_items)}件中、承認関連{len(approval_news)}件、その他{len(other_news)}件")
            logger.info(f"返却: {len(filtered_news)}件")
            
            return filtered_news
        
        except Exception as e:
            logger.error(f"ニュース取得に失敗: {e}")
            return []
    
    def get_chmp_highlights(self):
        """CHMP会議のハイライトを取得"""
        try:
            # CHMP会議ハイライトページのURLパターン
            chmp_search_url = f"{self.base_url}/en/search?search_api_views_fulltext=CHMP%20highlights"
            
            response = self._make_request(chmp_search_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 最新のCHMPハイライトリンクを検索
            chmp_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'chmp' in href.lower() and 'highlights' in href.lower():
                    full_url = urljoin(self.base_url, href)
                    chmp_links.append({
                        'title': link.get_text(strip=True),
                        'url': full_url
                    })
            
            return chmp_links[:5]  # 最新5件まで
        
        except Exception as e:
            logger.error(f"CHMPハイライト取得に失敗: {e}")
            return []