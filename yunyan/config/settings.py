import os
import json
from pathlib import Path
from colorama import Fore, Style, init
import openai
import time

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
            client = openai.Client(
                api_key=api_key,
                base_url=base_url
            )
            
            # 发送一个简单的测试请求
            start_time = time.time()
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
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
        
        while True:
            # 先获取 Base URL
            default_url = "https://api.deepseek.com/v1"
            base_url = input(f"{Fore.CYAN}请输入 API Base URL\n默认值 [{default_url}]: {Style.RESET_ALL}").strip()
            
            # 如果输入为空，使用默认值
            if not base_url:
                base_url = default_url
                print(f"{Fore.GREEN}使用默认 URL: {default_url}{Style.RESET_ALL}")
            elif not base_url.startswith('http'):
                print(f"{Fore.RED}请输入有效的 URL！必须以 http:// 或 https:// 开头{Style.RESET_ALL}")
                continue
            
            # 然后获取 API Key
            print(f"\n{Fore.YELLOW}提示：API Key 通常以 'sk-' 开头{Style.RESET_ALL}")
            while True:
                api_key = input(f"{Fore.CYAN}请输入你的 API Key: {Style.RESET_ALL}").strip()
                if api_key.startswith('sk-'):
                    break
                print(f"{Fore.RED}API Key 格式不正确！应该以 'sk-' 开头{Style.RESET_ALL}")
            
            # 验证 API 配置
            if self.validate_api(api_key, base_url):
                # 验证成功后保存配置
                self.set('api.base_url', base_url)
                self.set('api.key', api_key)
                print(f"\n{Fore.GREEN}配置已保存！{Style.RESET_ALL}")
                print(f"配置文件位置：{self.config_file}")
                return True
            
            # 验证失败，询问是否重试
            retry = input(f"\n{Fore.YELLOW}是否重新配置？(y/n): {Style.RESET_ALL}").strip().lower()
            if retry != 'y':
                print(f"\n{Fore.RED}配置未保存。程序退出。{Style.RESET_ALL}")
                return False
            print("\n" + "="*50 + "\n")
    
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