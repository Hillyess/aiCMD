import os
import json
from pathlib import Path

class Settings:
    def __init__(self):
        self.config_dir = Path.home() / '.yunyan'
        self.config_file = self.config_dir / 'config.json'
        self.default_config = {
            'api': {
                'key': 'sk-be29fe8884b247eaa01665aa2dd21139',
                'base_url': 'https://api.deepseek.com/v1'
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