import time
import threading
import os

class ThinkingTimer:
    def __init__(self, desc="AI 思考中"):
        self.desc = desc
        self.done = False
        self.start_time = None
        self._thread = None
        self.current_time = 0.0
        
        # 在 Windows 上启用 ANSI 颜色支持
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        
        # ANSI 颜色代码
        self.BLUE = "\033[34m"
        self.RESET = "\033[0m"
        self.CLEAR_LINE = "\033[K"
        self.CURSOR_UP = "\033[1A"

    def format_time(self, seconds):
        """将秒数格式化为时分秒"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        minutes = int(seconds // 60)
        seconds = seconds % 60
        if minutes < 60:
            return f"{minutes}分{seconds:.1f}秒"
        hours = int(minutes // 60)
        minutes = minutes % 60
        return f"{hours}时{minutes}分{seconds:.1f}秒"

    def animate(self):
        self.start_time = time.time()
        print("\n", end='', flush=True)
        
        while not self.done:
            self.current_time = time.time() - self.start_time
            print(f'\r{self.CURSOR_UP}{self.CLEAR_LINE}{self.BLUE}{self.desc} {self.format_time(self.current_time)}...{self.RESET}', 
                  end='\n', flush=True)
            time.sleep(0.1)
        
        print(f'\r{self.CURSOR_UP}{self.CLEAR_LINE}{self.BLUE}{self.desc} {self.format_time(self.current_time)} ✓{self.RESET}', 
              end='\n', flush=True)

    def start(self):
        self.done = False
        self._thread = threading.Thread(target=self.animate)
        self._thread.start()

    def stop(self):
        self.done = True
        if self._thread is not None:
            self._thread.join() 