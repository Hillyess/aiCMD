import requests
from urllib.parse import quote_plus
import re
from concurrent.futures import ThreadPoolExecutor
import time

class SearchEngine:
    """网络搜索引擎"""
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 可信域名列表
        self.trusted_domains = {
            'stackoverflow.com': 0.9,
            'github.com': 0.9,
            'docs.microsoft.com': 0.8,
            'linux.die.net': 0.8,
            'serverfault.com': 0.8,
            'superuser.com': 0.8,
            'askubuntu.com': 0.8,
            'digitalocean.com': 0.7,
            'redhat.com': 0.8,
            'ubuntu.com': 0.8,
            'debian.org': 0.8,
            'archlinux.org': 0.8,
            'kubernetes.io': 0.8,
            'docker.com': 0.8,
            'python.org': 0.9,
            'apache.org': 0.8,
            'nginx.com': 0.8,
            'elastic.co': 0.8
        }
        self.max_results = 5
        self.timeout = 10

    def search(self, query):
        """执行搜索
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            list: 搜索结果列表，每个结果包含 url, title, content 和 credibility
        """
        try:
            # 构建搜索 URL
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            # 发送请求
            response = requests.get(search_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 解析结果
            results = self._parse_results(response.text)
            
            # 并行获取页面内容
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(self._fetch_content, result)
                    for result in results[:self.max_results]
                ]
                
                detailed_results = []
                for future in futures:
                    try:
                        result = future.result(timeout=self.timeout)
                        if result:
                            detailed_results.append(result)
                    except Exception as e:
                        print(f"获取页面内容时出错: {str(e)}")
            
            # 按可信度排序
            detailed_results.sort(key=lambda x: x.get('credibility', 0), reverse=True)
            return detailed_results

        except Exception as e:
            print(f"搜索时出错: {str(e)}")
            return []

    def _parse_results(self, html):
        """解析搜索结果页面
        
        Args:
            html: 搜索结果页面的 HTML
            
        Returns:
            list: 初步的搜索结果列表
        """
        results = []
        
        # 使用正则表达式提取结果
        links = re.findall(r'<a class="result__url" href="([^"]+)".*?>(.*?)</a>', html)
        snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', html)
        
        for i, ((url, title), snippet) in enumerate(zip(links, snippets)):
            if i >= self.max_results:
                break
                
            # 计算可信度
            credibility = self._calculate_credibility(url)
            if credibility > 0:  # 只保留可信的结果
                results.append({
                    'url': url,
                    'title': self._clean_text(title),
                    'snippet': self._clean_text(snippet),
                    'credibility': credibility
                })
        
        return results

    def _fetch_content(self, result):
        """获取页面详细内容
        
        Args:
            result: 初步的搜索结果
            
        Returns:
            dict: 包含详细内容的结果
        """
        try:
            response = requests.get(
                result['url'], 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 提取正文内容（简单实现，可以使用更复杂的算法）
            content = re.sub(r'<[^>]+>', ' ', response.text)
            content = re.sub(r'\s+', ' ', content).strip()
            content = content[:1000]  # 限制长度
            
            result['content'] = content
            return result
            
        except Exception as e:
            print(f"获取 {result['url']} 的内容时出错: {str(e)}")
            return None

    def _calculate_credibility(self, url):
        """计算 URL 的可信度
        
        Args:
            url: 网页 URL
            
        Returns:
            float: 可信度分数 (0-1)
        """
        try:
            # 提取域名
            domain = re.search(r'https?://(?:www\.)?([^/]+)', url).group(1)
            
            # 检查是否是可信域名
            for trusted_domain, score in self.trusted_domains.items():
                if trusted_domain in domain:
                    return score
            
            # 其他域名的默认可信度
            return 0.5
            
        except Exception:
            return 0

    @staticmethod
    def _clean_text(text):
        """清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 替换 HTML 实体
        text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text 