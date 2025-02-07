
import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_segmentfault(query):
    """
    通过 SegmentFault 搜索相关技术问题
    """
    # 对查询关键词进行编码
    encoded_query = urllib.parse.quote(query)
    # 假设 SegmentFault 的搜索 URL 格式如下
    url = f"https://segmentfault.com/search?q={encoded_query}"
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.93 Safari/537.36"
        )
    }
    
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 根据 SegmentFault 的 HTML 结构选择合适的 CSS 选择器
            for item in soup.select('.search-result-item'):
                title_tag = item.select_one('.result-title a')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href')
                    # 如果链接为相对地址，则补全为绝对地址
                    if link and link.startswith('/'):
                        link = "https://segmentfault.com" + link
                    summary = item.select_one('.result-summary')
                    summary_text = summary.get_text(strip=True) if summary else ""
                    results.append({
                        "title": title,
                        "link": link,
                        "summary": summary_text
                    })
        else:
            print(f"[SegmentFault] 请求错误：{response.status_code}")
    except Exception as ex:
        print(f"[SegmentFault] 请求异常：{ex}")
    
    return results

def search_csdn(query):
    """
    通过 CSDN 搜索相关技术问题
    """
    encoded_query = urllib.parse.quote(query)
    # 假设 CSDN 搜索使用如下 URL（CSDN 搜索地址可能有多种，此处仅供示例）
    url = f"https://so.csdn.net/so/search/s.do?q={encoded_query}"
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.93 Safari/537.36"
        )
    }
    
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 根据 CSDN 的 HTML 结构提取搜索结果（选择器可能需要根据实际情况修改）
            for item in soup.select('.search-list-con'):
                title_tag = item.select_one('.title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href')
                    summary = item.select_one('.content')
                    summary_text = summary.get_text(strip=True) if summary else ""
                    results.append({
                        "title": title,
                        "link": link,
                        "summary": summary_text
                    })
        else:
            print(f"[CSDN] 请求错误：{response.status_code}")
    except Exception as ex:
        print(f"[CSDN] 请求异常：{ex}")
    
    return results

def search_problem(query):
    """
    综合查询技术问题解决方案，分别从 SegmentFault 和 CSDN 上搜集结果
    """
    print(f"正在查询问题：{query}")
    results_segmentfault = search_segmentfault(query)
    results_csdn = search_csdn(query)
    
    return {
        "segmentfault": results_segmentfault,
        "csdn": results_csdn
    }

if __name__ == "__main__":
    query = input("请输入需要查询的技术问题：")
    results = search_problem(query)
    
    print("\nSegmentFault 搜索结果：\n")
    for result in results["segmentfault"]:
        print(f"标题：{result['title']}")
        print(f"链接：{result['link']}")
        print(f"摘要：{result['summary']}\n")
        
    print("\nCSDN 搜索结果：\n")
    for result in results["csdn"]:
        print(f"标题：{result['title']}")
        print(f"链接：{result['link']}")
        print(f"摘要：{result['summary']}\n")