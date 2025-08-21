#!/usr/bin/env python3
"""
CBP501三相治験監視アプリケーション - スクレイピング処理
CBP501の三相治験開始情報のみに特化した検索
"""

import requests
import logging
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class CBP501Scraper:
    """CBP501三相治験情報専用スクレイピングクラス"""
    
    def __init__(self):
        self.base_url = "https://www.ema.europa.eu"
        self.search_urls = [
            f"{self.base_url}/en/news",
            f"{self.base_url}/en/human-regulatory/research-development/clinical-trials"
        ]
        self.session = requests.Session()
        
        # User-Agentを設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
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
                logger.debug(f"リクエスト成功: {len(response.content)} バイト取得")
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"リクエスト失敗 (試行 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ
                else:
                    raise
    
    def search_cbp501_phase3(self):
        """CBP501の三相治験情報を検索"""
        logger.info("CBP501三相治験情報の検索を開始")
        
        found_items = []
        
        # 複数のURLで検索
        for search_url in self.search_urls:
            try:
                logger.info(f"検索対象: {search_url}")
                response = self._make_request(search_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # ページ全体のテキストを取得
                page_text = soup.get_text().lower()
                
                # CBP501関連の情報を検索
                cbp501_items = self._find_cbp501_content(soup, search_url)
                found_items.extend(cbp501_items)
                
                logger.info(f"{search_url}での検索完了: {len(cbp501_items)}件発見")
                
            except Exception as e:
                logger.warning(f"検索エラー ({search_url}): {e}")
                continue
        
        # 結果の分析
        if found_items:
            logger.info(f"CBP501関連情報を合計{len(found_items)}件発見")
            
            # 三相治験関連のアイテムをフィルタリング
            phase3_items = self._filter_phase3_items(found_items)
            
            if phase3_items:
                logger.info(f"CBP501三相治験情報を{len(phase3_items)}件発見！")
                return True, phase3_items
            else:
                logger.info("CBP501情報は見つかりましたが、三相治験関連ではありませんでした")
                return False, found_items  # 参考情報として返す
        
        logger.info("CBP501に関する情報は見つかりませんでした")
        return False, []
    
    def _find_cbp501_content(self, soup, source_url):
        """ページからCBP501関連コンテンツを検索"""
        cbp501_items = []
        
        # CBP501を含むリンクを検索
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get('href')
            
            if self._contains_cbp501(text):
                full_url = urljoin(self.base_url, href)
                cbp501_items.append({
                    'type': 'link',
                    'title': text,
                    'url': full_url,
                    'source': source_url,
                    'content': text
                })
                logger.debug(f"CBP501リンク発見: {text[:100]}...")
        
        # CBP501を含むテキスト要素を検索
        all_text_elements = soup.find_all(['p', 'div', 'span', 'li'])
        
        for element in all_text_elements:
            text = element.get_text(strip=True)
            
            if self._contains_cbp501(text) and len(text) > 20:
                # 関連するリンクを検索
                related_link = element.find('a') or element.find_parent('a')
                url = ""
                if related_link and related_link.get('href'):
                    url = urljoin(self.base_url, related_link['href'])
                
                cbp501_items.append({
                    'type': 'text',
                    'title': text[:100] + ('...' if len(text) > 100 else ''),
                    'url': url,
                    'source': source_url,
                    'content': text
                })
                logger.debug(f"CBP501テキスト発見: {text[:100]}...")
        
        return cbp501_items
    
    def _contains_cbp501(self, text):
        """テキストにCBP501が含まれているかチェック"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # CBP501の様々な表記パターン
        cbp501_patterns = [
            'cbp501',
            'cbp-501', 
            'cbp 501',
            'cbp501',
            # 念のため他の表記も
            'cb-p501',
            'cb p501'
        ]
        
        return any(pattern in text_lower for pattern in cbp501_patterns)
    
    def _filter_phase3_items(self, items):
        """三相治験関連のアイテムをフィルタリング"""
        phase3_items = []
        
        # 三相治験を示すキーワード
        phase3_keywords = [
            'phase 3', 'phase iii', 'phase three',
            'phase-3', 'phase-iii', 'phaseiii',
            'p3', 'piii',
            '3相', '三相', 'III相',
            'pivotal', 'registration', 'confirmatory'
        ]
        
        # 治験開始を示すキーワード
        trial_start_keywords = [
            'start', 'initiat', 'begin', 'launch', 'commence',
            '開始', 'スタート', '着手', '実施',
            'first patient', 'enrollment', 'recruit'
        ]
        
        for item in items:
            content_lower = item['content'].lower()
            
            # 三相治験のキーワードをチェック
            has_phase3 = any(keyword in content_lower for keyword in phase3_keywords)
            
            # 治験開始のキーワードをチェック
            has_trial_start = any(keyword in content_lower for keyword in trial_start_keywords)
            
            if has_phase3 or has_trial_start:
                # より詳細な分析結果を追加
                item['phase3_keywords'] = [kw for kw in phase3_keywords if kw in content_lower]
                item['start_keywords'] = [kw for kw in trial_start_keywords if kw in content_lower]
                item['confidence'] = 'high' if (has_phase3 and has_trial_start) else 'medium'
                
                phase3_items.append(item)
                logger.info(f"三相治験候補発見: {item['title'][:50]}... (信頼度: {item['confidence']})")
        
        return phase3_items