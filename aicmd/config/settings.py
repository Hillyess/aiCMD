import os
import json
from pathlib import Path
from colorama import Fore, Style, init
import openai
import time
import requests

# 初始化 colorama
init()

class Settings:
    def __init__(self):
        self.config_dir = Path.home() / '.aicmd'  # 改为 .aicmd
        self.config_file = self.config_dir / 'config.json'
        self.default_config = {
            'api': {
                'key': '',  # 移除默认 API key
                'base_url': ''  # 移除默认 base URL
            },
            'display': {
                'emoji_support': True,
                'color_support': True
            },
            'history': {
                'max_entries': 1000,
                'save_file': True
            }
        }
        self.load_config()
        
    def validate_api(self, api_key, base_url):
        """验证 API 配置是否可用"""
        try:
            print(f"\n{Fore.YELLOW}正在验证 API 配置...{Style.RESET_ALL}")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {
                        "role": "user",
                        "content": "hi"
                    }
                ],
                "max_tokens": 10
            }
            
            start_time = time.time()
            response = requests.post(
                base_url,
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            latency = time.time() - start_time
            
            print(f"{Fore.GREEN}✓ API 连接成功！延迟: {latency:.2f}秒{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                print(f"{Fore.RED}✗ API Key 无效或未授权{Style.RESET_ALL}")
            elif "404" in error_msg:
                print(f"{Fore.RED}✗ API 地址无法访问{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ API 验证失败: {error_msg}{Style.RESET_ALL}")
            return False

    def setup_wizard(self):
        """首次运行配置向导"""
        print(f"\n{Fore.GREEN}=== aiCMD 首次运行配置向导 ==={Style.RESET_ALL}")
        print("请配置 AI API 信息：")
        
        # 设置默认值
        default_url = "https://api.siliconflow.cn/v1/chat/completions"
        default_key = "sk-nayyjjucvglfvvgehztuqbxicvruerbjqrzswhfpsecpghaj"
        
        # 保存配置
        self.set('api.base_url', default_url)
        self.set('api.key', default_key)
        
        print(f"{Fore.GREEN}使用默认配置：{Style.RESET_ALL}")
        print(f"URL: {default_url}")
        print(f"API Key: {default_key}")
        print(f"\n{Fore.GREEN}配置已保存！{Style.RESET_ALL}")
        print(f"配置文件位置：{self.config_file}")
        return True

    def load_config(self):
        """加载配置"""
        try:
            if not self.config_file.exists():
                self.save_config(self.default_config)
            
            with open(self.config_file) as f:
                self.config = json.load(f)
        except Exception:
            self.config = self.default_config.copy()
    
    def save_config(self, config):
        """保存配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception:
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except Exception:
            return default
    
    def set(self, key, value):
        """设置配置值"""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                config = config.setdefault(k, {})
            config[keys[-1]] = value
            self.save_config(self.config)
            return True
        except Exception:
            return False
            
    def check_api_config(self):
        """检查 API 配置是否完整"""
        api_key = self.get('api.key')
        base_url = self.get('api.base_url')
        return bool(api_key and base_url)

    def clear_api_config(self):
        """清除 API 配置"""
        self.set('api.key', '')
        self.set('api.base_url', '')
        return True 