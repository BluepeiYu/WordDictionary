# spider.py
import time
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import quote

class OnlineDictionarySpider:
    def __init__(self):
        self.ua = UserAgent()
        self.last_request_time = 0
        self.request_interval = 1.5  # 请求间隔(秒)

    def _get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://dictionary.cambridge.org/'
        }

    def fetch_definition(self, word):
        """ 主爬取方法 """
        try:
            # 遵守爬虫速率限制
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.request_interval:
                time.sleep(self.request_interval - time_since_last)
            
            encoded_word = quote(word.lower())
            url = f"https://dictionary.cambridge.org/dictionary/english-chinese-simplified/{encoded_word}"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            return self._parse_html(response.text)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"error": "单词不存在"}
            return {"error": f"HTTP错误: {str(e)}"}
        except Exception as e:
            return {"error": f"抓取失败: {str(e)}"}

    def _parse_html(self, html):
        """ 解析HTML的核心方法 """
        soup = BeautifulSoup(html, 'lxml')
        result = {
            "definitions": [],
            "examples": []
        }

        # 解析释义
        definition_blocks = soup.select('.def-block')
        for block in definition_blocks[:3]:  # 取前3个释义
            definition = block.select_one('.def').text.strip()
            translation = block.select_one('.trans').text.strip()
            result["definitions"].append(f"{definition}\n{translation}")

        # 解析例句
        example_blocks = soup.select('.examp')
        for ex in example_blocks[:2]:  # 取前2个例句
            english = ex.select_one('.eg').text.strip()
            chinese = ex.select_one('.trans').text.strip()
            result["examples"].append(f"• {english}\n  {chinese}")

        if not result["definitions"]:
            return {"error": "解析失败"}
        return result

if __name__ == '__main__':
    # 测试用例
    spider = OnlineDictionarySpider()
    test_words = ["ambition", "synchronize", "notexistword"]
    
    for word in test_words:
        print(f"\n=== 测试单词: {word} ===")
        data = spider.fetch_definition(word)
        if "error" in data:
            print(f"错误: {data['error']}")
        else:
            print("[释义]")
            print("\n".join(data["definitions"]))
            print("\n[例句]")
            print("\n\n".join(data["examples"]))
        time.sleep(2)