#!/usr/bin/env python3
"""
EMA承認監視アプリケーション - デバッグ用スクレイピング
EMAサイトの構造を詳しく分析する
"""

import requests
import logging
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# ログ設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EMADebugScraper:
    """EMAサイトのデバッグ用スクレイピングクラス"""
    
    def __init__(self):
        self.base_url = "https://www.ema.europa.eu"
        self.news_url = f"{self.base_url}/en/news"
        self.session = requests.Session()
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def debug_page_structure(self):
        """ページ構造を詳しく分析"""
        try:
            print("=== EMAニュースページ構造分析 ===")
            
            response = self.session.get(self.news_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✅ ページ取得成功: {len(response.content)} バイト")
            
            # 基本的な要素の確認
            print(f"\n📊 基本統計:")
            print(f"  - 総要素数: {len(soup.find_all())}")
            print(f"  - div要素数: {len(soup.find_all('div'))}")
            print(f"  - リンク数: {len(soup.find_all('a'))}")
            print(f"  - 見出し数: {len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))}")
            
            # クラス名の分析
            print(f"\n🏷️ 重要なクラス名:")
            class_patterns = ['view', 'content', 'news', 'item', 'article', 'listing', 'card']
            
            for pattern in class_patterns:
                elements = soup.find_all(attrs={'class': re.compile(pattern, re.I)})
                if elements:
                    print(f"  - '{pattern}' 関連: {len(elements)}個")
                    # 最初の要素のクラス名を表示
                    if elements[0].get('class'):
                        print(f"    例: {' '.join(elements[0]['class'])}")
            
            # view-contentの詳細分析
            view_content = soup.find('div', class_=re.compile(r'view-content'))
            if view_content:
                print(f"\n🎯 view-content分析:")
                print(f"  - クラス: {view_content.get('class')}")
                print(f"  - 子要素数: {len(view_content.find_all())}")
                print(f"  - 直接の子div: {len(view_content.find_all('div', recursive=False))}")
                print(f"  - 内部のリンク: {len(view_content.find_all('a'))}")
                
                # 最初のいくつかのリンクを詳細表示
                links = view_content.find_all('a', href=True)[:5]
                print(f"\n  📎 最初の5個のリンク:")
                for i, link in enumerate(links, 1):
                    href = link.get('href')
                    text = link.get_text(strip=True)[:60]
                    print(f"    {i}. {text}...")
                    print(f"       URL: {href}")
                    
                    # 親要素の情報
                    parent = link.parent
                    if parent:
                        parent_class = parent.get('class', [])
                        print(f"       親要素: {parent.name} (class: {parent_class})")
            
            # main要素の分析
            main_element = soup.find('main')
            if main_element:
                print(f"\n📄 main要素分析:")
                print(f"  - クラス: {main_element.get('class')}")
                print(f"  - 子要素数: {len(main_element.find_all())}")
                
                # main内の見出しを検索
                headings = main_element.find_all(['h1', 'h2', 'h3', 'h4'])
                print(f"  - 見出し数: {len(headings)}")
                
                if headings:
                    print(f"  📰 最初の3個の見出し:")
                    for i, heading in enumerate(headings[:3], 1):
                        text = heading.get_text(strip=True)[:80]
                        print(f"    {i}. {heading.name}: {text}...")
                        
                        # 関連するリンクを検索
                        link = heading.find('a') or heading.find_next('a')
                        if link:
                            print(f"       リンク: {link.get('href')}")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False
    
    def extract_sample_news(self):
        """サンプルニュースを抽出してテスト"""
        try:
            print("\n=== サンプルニュース抽出テスト ===")
            
            response = self.session.get(self.news_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 複数のアプローチでニュースを抽出
            approaches = [
                ("view-content内のリンク", self._extract_from_view_content),
                ("見出しベース", self._extract_from_headings),
                ("全リンク検索", self._extract_from_all_links)
            ]
            
            for approach_name, extract_func in approaches:
                print(f"\n🔍 {approach_name}アプローチ:")
                items = extract_func(soup)
                print(f"  抽出数: {len(items)}件")
                
                for i, item in enumerate(items[:3], 1):
                    print(f"  {i}. {item['title'][:60]}...")
                    print(f"     URL: {item['link']}")
                    print(f"     承認関連: {'はい' if item['is_approval_related'] else 'いいえ'}")
            
            return True
            
        except Exception as e:
            print(f"❌ サンプル抽出エラー: {e}")
            return False
    
    def _extract_from_view_content(self, soup):
        """view-contentからの抽出"""
        items = []
        view_content = soup.find('div', class_=re.compile(r'view-content'))
        if view_content:
            links = view_content.find_all('a', href=True)
            for i, link in enumerate(links[:10]):
                if '/news/' in link.get('href', ''):
                    item = self._create_item_from_link(link, f"vc_{i}")
                    if item:
                        items.append(item)
        return items
    
    def _extract_from_headings(self, soup):
        """見出しからの抽出"""
        items = []
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for i, heading in enumerate(headings[:10]):
            link = heading.find('a') or heading.find_next('a')
            if link and link.get('href'):
                item = self._create_item_from_link(link, f"h_{i}")
                if item:
                    items.append(item)
        return items
    
    def _extract_from_all_links(self, soup):
        """全リンクからの抽出"""
        items = []
        links = soup.find_all('a', href=True)
        processed = set()
        
        for i, link in enumerate(links):
            href = link.get('href', '')
            if ('/news/' in href and 
                href not in processed and 
                len(link.get_text(strip=True)) > 10):
                
                processed.add(href)
                item = self._create_item_from_link(link, f"all_{i}")
                if item:
                    items.append(item)
                    if len(items) >= 10:
                        break
        return items
    
    def _create_item_from_link(self, link, prefix):
        """リンクからアイテムを作成"""
        try:
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                return None
            
            href = link.get('href')
            full_url = urljoin(self.base_url, href)
            
            # 承認関連キーワードのチェック
            approval_keywords = [
                'recommended for approval', 'positive opinion', 'marketing authorisation',
                'new medicine', 'chmp', 'committee for medicinal products',
                'approved', 'authorisation', 'recommendation', 'conditional marketing'
            ]
            
            is_approval_related = any(keyword in title.lower() for keyword in approval_keywords)
            
            return {
                'id': f"{prefix}_{hash(title + full_url)}",
                'title': title,
                'link': full_url,
                'date': "",
                'description': "",
                'is_approval_related': is_approval_related
            }
            
        except Exception as e:
            return None

def main():
    """デバッグスクリプトのメイン関数"""
    print("🔍 EMA サイト構造デバッグツール")
    print("=" * 50)
    
    scraper = EMADebugScraper()
    
    # ページ構造の分析
    print("1️⃣ ページ構造分析を実行中...")
    success1 = scraper.debug_page_structure()
    
    # サンプルニュース抽出
    print("\n2️⃣ サンプルニュース抽出を実行中...")
    success2 = scraper.extract_sample_news()
    
    # 結果まとめ
    print("\n" + "=" * 50)
    print("📊 デバッグ結果まとめ")
    print("=" * 50)
    
    if success1:
        print("✅ ページ構造分析: 成功")
    else:
        print("❌ ページ構造分析: 失敗")
    
    if success2:
        print("✅ サンプルニュース抽出: 成功")
    else:
        print("❌ サンプルニュース抽出: 失敗")
    
    if success1 and success2:
        print("\n🎉 デバッグ完了！上記の情報を基にscraper.pyを調整してください。")
    else:
        print("\n⚠️ 問題が検出されました。ネットワーク接続やサイト構造を確認してください。")

if __name__ == "__main__":
    main()