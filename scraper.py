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
            # EMAサイトの実際の構造に基づいた複数のアプローチ
            logger.info("ニュース項目の抽出を開始...")
            
            # アプローチ1: view-content内のすべてのリンクを検索
            view_content = soup.find('div', class_=re.compile(r'view-content'))
            if view_content:
                logger.info("view-contentコンテナを発見")
                links = view_content.find_all('a', href=True)
                logger.info(f"view-content内のリンク数: {len(links)}")
                
                processed_urls = set()  # 重複避け
                
                for idx, link in enumerate(links):
                    try:
                        href = link.get('href')
                        if not href or href in processed_urls:
                            continue
                        
                        # EMAニュースページのURLパターンをチェック
                        if '/news/' not in href and '/en/news/' not in href:
                            continue
                        
                        processed_urls.add(href)
                        
                        # リンクからニュース項目を構築
                        item = self._parse_link_item(link, idx)
                        if item:
                            news_items.append(item)
                            
                    except Exception as e:
                        logger.warning(f"リンク解析に失敗 (項目 {idx}): {e}")
                        continue
            
            # アプローチ2: 見出しタグを基準にした抽出
            if len(news_items) < 5:
                logger.info("見出しタグからの抽出を試行...")
                headings = soup.find_all(['h2', 'h3', 'h4'])
                
                for idx, heading in enumerate(headings[:15]):
                    try:
                        # 見出しに関連するリンクを検索
                        link = heading.find('a') or heading.find_next('a')
                        if link and link.get('href'):
                            item = self._parse_heading_item(heading, link, idx + 1000)
                            if item and item not in news_items:
                                news_items.append(item)
                    except Exception as e:
                        logger.warning(f"見出し解析に失敗 (項目 {idx}): {e}")
                        continue
            
            # アプローチ3: より広範な検索
            if len(news_items) < 3:
                logger.info("広範なリンク検索を実行...")
                all_links = soup.find_all('a', href=True)
                
                for idx, link in enumerate(all_links[:50]):
                    try:
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        
                        # EMAニュース関連のURLを検索
                        if (('/news/' in href or '/en/news/' in href) and 
                            len(text) > 10 and 
                            not any(item['link'] == urljoin(self.base_url, href) for item in news_items)):
                            
                            item = self._parse_generic_link(link, idx + 2000)
                            if item:
                                news_items.append(item)
                                
                    except Exception as e:
                        continue
            
            logger.info(f"最終的に {len(news_items)} 件のニュース項目を抽出")
            
        except Exception as e:
            logger.error(f"ニュース項目の抽出に失敗: {e}")
        
        return news_items
    
    def _parse_link_item(self, link, idx):
        """リンク要素からニュース項目を解析"""
        try:
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                return None
            
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            
            # 周辺のコンテキストから説明文を検索
            description = ""
            parent = link.parent
            if parent:
                # 同じ親要素内の他のテキストを検索
                text_elements = parent.find_all(text=True)
                combined_text = ' '.join([t.strip() for t in text_elements if t.strip()])
                if len(combined_text) > len(title):
                    description = combined_text[:200] + "..."
            
            # 日付情報を検索
            date_text = ""
            date_patterns = [
                r'\d{1,2}\s+\w+\s+\d{4}',  # "25 July 2025"
                r'\d{4}-\d{2}-\d{2}',      # "2025-07-25"
                r'\w+\s+\d{4}'             # "July 2025"
            ]
            
            if parent:
                parent_text = parent.get_text()
                for pattern in date_patterns:
                    match = re.search(pattern, parent_text)
                    if match:
                        date_text = match.group()
                        break
            
            # 承認関連キーワードのチェック
            content_text = (title + " " + description).lower()
            approval_keywords = [
                'recommended for approval', 'positive opinion', 'marketing authorisation',
                'new medicine', 'chmp', 'committee for medicinal products',
                'approved', 'authorisation', 'recommendation', 'conditional marketing',
                'orphan medicine', 'biosimilar', 'generic medicine'
            ]
            
            is_approval_related = any(keyword in content_text for keyword in approval_keywords)
            
            return {
                'id': f"link_{idx}_{hash(title + full_url)}",
                'title': title,
                'link': full_url,
                'date': date_text,
                'description': description,
                'is_approval_related': is_approval_related
            }
            
        except Exception as e:
            logger.warning(f"リンク項目の解析エラー: {e}")
            return None
    
    def _parse_heading_item(self, heading, link, idx):
        """見出し要素からニュース項目を解析"""
        try:
            title = heading.get_text(strip=True)
            if not title or len(title) < 10:
                return None
            
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            
            # 見出しの次の要素から説明文を検索
            description = ""
            next_element = heading.find_next(['p', 'div'])
            if next_element:
                desc_text = next_element.get_text(strip=True)
                if desc_text and len(desc_text) > 20:
                    description = desc_text[:200] + "..."
            
            # 承認関連キーワードのチェック
            content_text = (title + " " + description).lower()
            approval_keywords = [
                'recommended for approval', 'positive opinion', 'marketing authorisation',
                'new medicine', 'chmp', 'committee for medicinal products',
                'approved', 'authorisation', 'recommendation'
            ]
            
            is_approval_related = any(keyword in content_text for keyword in approval_keywords)
            
            return {
                'id': f"heading_{idx}_{hash(title + full_url)}",
                'title': title,
                'link': full_url,
                'date': "",
                'description': description,
                'is_approval_related': is_approval_related
            }
            
        except Exception as e:
            logger.warning(f"見出し項目の解析エラー: {e}")
            return None
    
    def _parse_generic_link(self, link, idx):
        """一般的なリンクからニュース項目を解析"""
        try:
            title = link.get_text(strip=True)
            if not title or len(title) < 15:
                return None
            
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            
            # 承認関連キーワードのチェック
            content_text = title.lower()
            approval_keywords = [
                'recommended for approval', 'positive opinion', 'marketing authorisation',
                'new medicine', 'chmp', 'committee for medicinal products',
                'approved', 'authorisation', 'recommendation'
            ]
            
            is_approval_related = any(keyword in content_text for keyword in approval_keywords)
            
            return {
                'id': f"generic_{idx}_{hash(title + full_url)}",
                'title': title,
                'link': full_url,
                'date': "",
                'description': "",
                'is_approval_related': is_approval_related
            }
            
        except Exception as e:
            logger.warning(f"一般リンク項目の解析エラー: {e}")
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