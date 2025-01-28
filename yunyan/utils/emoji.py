import sys
import locale
import os

class EmojiSupport:
    def __init__(self):
        self.has_emoji_support = self._check_emoji_support()
        
        # emoji 到文字的映射
        self.text_fallbacks = {
            '🤖': '[AI] ',    # 添加空格
            '👋': '[再见] ',  # 添加空格
            '💡': '[提示] ',  # 添加空格
            '💻': '[命令] ',  # 添加空格
            '✓': '[完成] ',   # 添加空格
            '🔍': '[搜索] ',  # 添加空格
            '❌': '[错误] ',  # 添加空格
            '⚠️': '[警告] '   # 添加空格
        }
    
    def get(self, emoji):
        """获取 emoji 或其文字替代"""
        if self.has_emoji_support:
            # 在 Linux 下添加额外的空格
            if os.name != 'nt':
                return f"{emoji} "  # 添加空格
            return emoji
        return self.text_fallbacks.get(emoji, '[?] ')  # 添加空格
    
    def _check_emoji_support(self):
        """检查终端是否支持 emoji"""
        if os.name == 'nt':  # Windows
            return self._check_windows_terminal()
        else:  # Unix-like
            return self._check_unix_terminal()
    
    def _check_windows_terminal(self):
        """检查 Windows 终端是否支持 emoji"""
        if 'WT_SESSION' in os.environ:  # Windows Terminal
            return True
        if 'TERM_PROGRAM' in os.environ:  # VSCode
            return True
        try:
            import platform
            win_ver = int(platform.version().split('.')[0])
            return win_ver >= 10
        except:
            return False
    
    def _check_unix_terminal(self):
        """检查 Unix 终端是否支持 emoji"""
        term = os.environ.get('TERM', '')
        if 'xterm' in term or 'linux' in term:
            try:
                current_locale = locale.getlocale()[1]
                return current_locale and 'UTF-8' in current_locale.upper()
            except:
                return False
        return False 