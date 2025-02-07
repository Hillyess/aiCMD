import os
import sys
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from colorama import init, Fore, Style
from ..utils.emoji import EmojiSupport
import time
from .base import BaseTerminal  # 从 base.py 导入基类
import platform

# 初始化 colorama 以支持 Windows 彩色输出
init()

class WindowsTerminal(BaseTerminal):
    """Windows 专用终端实现"""
    def __init__(self, callback=None, agent_mode=False):
        super().__init__(callback, agent_mode)
        self.emoji = EmojiSupport()
        self.thinking_time = None
        self.agent_mode = agent_mode  # 确保 agent_mode 被设置
        
        # 设置历史文件
        history_file = os.path.expanduser('~/.aicmd_history')
        
        # 创建会话
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            key_bindings=self._create_key_bindings(),
            style=self._create_style(),
            complete_in_thread=True,
            complete_while_typing=False,
            enable_history_search=True,
            mouse_support=True,
            refresh_interval=0.5,
        )
        
        # 创建补全器并传入 session
        self.completer = self._create_completer()
        
        # 设置补全器
        self.session.completer = self.completer
        
        # 添加历史记录跟踪
        self.command_history = []
        self.output_history = []
        self.chat_history = []

    def _create_completer(self):
        """创建 Windows 补全器"""
        class WindowsCompleter(Completer):
            def __init__(self, session):
                self.session = session  # 保存 session 引用
                self.completion_cache = set()  # 添加缓存集合
                
            def get_completions(self, document, complete_event):
                word = document.get_word_before_cursor()
                text_before_cursor = document.text_before_cursor
                
                # 先检查是否是历史命令补全
                if word and not text_before_cursor.startswith(('cd ', 'dir ')):
                    # 从会话历史记录中查找匹配的命令
                    history = self.session.history.get_strings()
                    for cmd in reversed(history):  # 倒序遍历，最新的命令优先
                        if cmd.startswith(word) and cmd not in self.completion_cache:
                            self.completion_cache.add(cmd)  # 添加到缓存
                            yield Completion(
                                cmd,
                                start_position=-len(word),
                                display_meta='history'
                            )
                
                # 然后是路径补全
                if text_before_cursor.startswith('cd ') or text_before_cursor.startswith('dir '):
                    # 路径补全
                    cmd_parts = text_before_cursor.split(maxsplit=1)
                    path = cmd_parts[1] if len(cmd_parts) > 1 else ''
                    
                    # 处理路径
                    if path.startswith('~'):
                        base_dir = os.path.expanduser(path)
                    elif path.startswith('/') or path.startswith('\\'):
                        base_dir = path
                    else:
                        base_dir = os.path.join(os.getcwd(), path)
                    
                    try:
                        # 获取目录内容
                        if os.path.isdir(base_dir):
                            dirname, basename = base_dir, ''
                        else:
                            dirname, basename = os.path.split(base_dir)
                        
                        if not os.path.exists(dirname):
                            dirname = os.getcwd()
                        
                        items = os.listdir(dirname)
                        items = [
                            item for item in items
                            if item.lower().startswith(basename.lower())
                        ]
                        
                        # 生成补全项
                        for item in sorted(items):
                            full_path = os.path.join(dirname, item)
                            is_dir = os.path.isdir(full_path)
                            
                            # 使用 Windows 风格路径
                            if path.startswith('/') or path.startswith('\\'):
                                completion = full_path.replace('/', '\\')
                            else:
                                completion = os.path.relpath(full_path).replace('/', '\\')
                            
                            if is_dir:
                                completion += '\\'
                                
                            yield Completion(
                                completion,
                                start_position=-len(path),
                                display=item + ('\\' if is_dir else ''),
                                display_meta='dir' if is_dir else 'file'
                            )
                            
                    except Exception:
                        pass
                        
                else:
                    # Windows 命令补全
                    windows_commands = [
                        'dir', 'cd', 'copy', 'del', 'echo', 'exit', 'help',
                        'md', 'mkdir', 'move', 'path', 'pause', 'print',
                        'rd', 'ren', 'rename', 'rmdir', 'start', 'time',
                        'type', 'ver', 'vol', 'date', 'cls', 'color'
                    ]
                    
                    for cmd in windows_commands:
                        if cmd.startswith(word.lower()):
                            yield Completion(cmd, start_position=-len(word))
        
        # 创建补全器实例时传入 session
        return WindowsCompleter(self.session)

    def _create_style(self):
        """创建提示符样式"""
        return PromptStyle.from_dict({
            'ansiyellow': 'ansibrightyellow bold',
            'ansiblue': 'ansibrightblue bold',
            'prompt': 'ansiwhite',
            'ai': 'ansibrightmagenta bold'
        })

    def _create_key_bindings(self):
        """创建按键绑定"""
        bindings = KeyBindings()
        
        # 添加双击 Ctrl+C 检测
        self.last_ctrl_c_time = 0
        
        @bindings.add('c-c')
        def _(event):
            """处理 Ctrl+C"""
            current_time = time.time()
            if current_time - self.last_ctrl_c_time < 0.5:  # 0.5秒内双击
                print(f"\n{self.emoji.get('👋')} 再见！")
                event.app.exit()
                # 强制退出程序
                import sys
                sys.exit(0)
            else:
                self.last_ctrl_c_time = current_time
                print('^C')
            
        @bindings.add('c-d')
        def _(event):
            """处理 Ctrl+D"""
            print(f"\n{self.emoji.get('👋')} 再见！")
            event.app.exit()
            # 强制退出程序
            import sys
            sys.exit(0)
            
        @bindings.add('tab')
        def _(event):
            b = event.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=False)
                
        @bindings.add('right')
        def _(event):
            b = event.current_buffer
            if b.complete_state and b.complete_state.current_completion:
                completion = b.complete_state.current_completion
                b.apply_completion(completion)
                if completion.text.endswith('\\'):
                    b.start_completion(select_first=False)
                else:
                    b.complete_state = None
                    
        @bindings.add('space')
        def _(event):
            b = event.current_buffer
            if b.complete_state and b.complete_state.current_completion:
                completion = b.complete_state.current_completion
                b.apply_completion(completion)
                if completion.text.endswith('\\'):
                    b.start_completion(select_first=False)
                else:
                    b.insert_text(' ')
                    b.complete_state = None
            else:
                b.insert_text(' ')
                
        return bindings

    def _capture_output(self, command):
        """捕获 Windows 命令输出"""
        try:
            # 使用 PowerShell 执行命令，关闭 PowerShell 的进度显示
            powershell_command = (
                'powershell.exe -NoProfile -NonInteractive -Command "'
                '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; '  # 设置输出编码
                '$ProgressPreference = \'SilentlyContinue\'; '  # 关闭进度显示，使用引号
                f'& {{ {command} }}"'  # 使用 ScriptBlock 执行命令
            )
            
            # 创建环境变量副本并设置编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                powershell_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding='gbk',  # Windows 默认使用 GBK
                errors='replace',
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            output = []
            while True:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    # 处理编码
                    try:
                        print(stdout_line, end='', flush=True)
                        output.append(stdout_line)
                    except UnicodeEncodeError:
                        # 如果 GBK 失败，尝试 UTF-8
                        print(stdout_line.encode('utf-8', errors='replace').decode('utf-8', errors='replace'), end='', flush=True)
                        output.append(stdout_line)
                
                stderr_line = process.stderr.readline()
                if stderr_line:
                    output.append(stderr_line)
                
                if process.poll() is not None:
                    for line in process.stdout.readlines():
                        try:
                            print(line, end='', flush=True)
                            output.append(line)
                        except UnicodeEncodeError:
                            print(line.encode('utf-8', errors='replace').decode('utf-8', errors='replace'), end='', flush=True)
                            output.append(line)
                    for line in process.stderr.readlines():
                        output.append(line)
                    break
            
            process.wait()
            return ''.join(output)
            
        except Exception as e:
            error_msg = str(e)
            print(error_msg, file=sys.stderr)
            return error_msg

    def get_prompt(self):
        """获取命令提示符"""
        # 根据模式选择不同的机器人表情
        if self.agent_mode:
            robot = '️️A'  # Agent模式
        else:
            robot = 'Q'  # 问答模式
            
        # 获取基本信息
        username = os.getlogin()
        hostname = platform.node()
        cwd = os.getcwd()
        
        # 使用 FormattedText 构建提示符
        return FormattedText([
            ('', f'{self.emoji.get(robot)} '),  # 机器人表情
            ('', '(ai) '),  # 固定标识
            ('class:ansiyellow', f'{username}@{hostname}'),  # 用户名和主机名（黄色）
            ('', ':'),
            ('class:ansiblue', cwd),  # 当前目录（蓝色）
            ('class:prompt', ' $ ')  # 提示符
        ])

    def _build_context(self):
        """构建上下文信息"""
        context = []
        
        context.append("=== 系统环境 ===")
        context.append(f"当前目录: {os.getcwd()}")
        context.append(f"Windows版本: {sys.getwindowsversion().major}.{sys.getwindowsversion().minor}")
        context.append("")
        
        context.append("=== 最近操作 ===")
        for i, (cmd, output) in enumerate(zip(self.command_history[-5:], self.output_history[-5:])):
            context.append(f"命令[{i+1}]: {cmd}")
            if output.strip():
                context.append(f"输出[{i+1}]:\n{output.strip()}")
            context.append("")
        
        if self.chat_history:
            context.append("=== 对话历史 ===")
            for i, (q, a) in enumerate(self.chat_history[-3:]):
                context.append(f"问题[{i+1}]: {q}")
                context.append(f"回答[{i+1}]: {a}")
                context.append("")
        
        return "\n".join(context)

    def run(self):
        """运行终端"""
        try:
            self.show_welcome()
            while True:
                try:
                    command = self.session.prompt(
                        self.get_prompt(),  # 使用 self.get_prompt()
                        enable_suspend=True,
                        enable_open_in_editor=True,
                        complete_while_typing=False,
                        complete_in_thread=True
                    )
                    
                    if not command:
                        continue
                        
                    if command.strip() == 'exit':
                        print(f"\n{self.emoji.get('👋')} 再见！")
                        break
                    
                    # 检查第一个字符是否是中文
                    first_char = command[0] if command else ''
                    is_chinese = '\u4e00' <= first_char <= '\u9fff'
                    
                    # 记录命令
                    self.command_history.append(command)
                        
                    if command.startswith('/') or is_chinese:
                        # AI 问答模式
                        query = command[1:] if command.startswith('/') else command
                        if self.callback:
                            context = self._build_context()
                            response = self.callback(query)
                            
                            # 如果是 Agent 模式，等待用户执行命令后再继续
                            if hasattr(self, 'agent_mode') and self.agent_mode:
                                continue  # 直接返回到命令行，让用户执行命令
                    else:
                        # 执行命令并记录输出
                        output = self._capture_output(command)
                        self.output_history.append(output)
                        print(output, end='')
                        
                        # 如果是 Agent 模式，将结果发送给 AI 分析
                        if hasattr(self, 'agent_mode') and self.agent_mode and self.callback:
                            self.callback(f"命令 '{command}' 已执行，输出为：\n{output}\n请分析结果并告诉我下一步该怎么做。")
                            
                except KeyboardInterrupt:
                    print('^C')
                    continue
                except EOFError:
                    print(f"\n{self.emoji.get('👋')} 再见！")
                    break
                    
        except Exception as e:
            print(f"{Fore.RED}运行时错误: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)

    def show_welcome(self):
        """显示欢迎信息"""
        # 使用 colorama 的 ANSI 颜色代码
        print(f"\n=== \033[96maiCMD智能运维助手\033[0m ===")
        print(f"{self.emoji.get('👋')} 欢迎使用aiCMD！")
        if self.agent_mode:
            print(f"{self.emoji.get('🤖')} \033[92m已进入 Agent 模式\033[0m")
            print(f"{self.emoji.get('💡')} 直接描述你想完成的任务即可")
            print(f"示例：\033[96m安装并配置 Nginx 服务器\033[0m")
        else:
            print(f"{self.emoji.get('💡')} 输入 / 开头的内容可以询问 AI")
            print(f"{self.emoji.get('💻')} 输入 'exit' 退出程序")
            print(f"示例：\033[96m/如何查看系统状态\033[0m")
        print("=====================\n")

    def set_thinking_time(self, time):
        """设置思考时间"""
        self.thinking_time = time 

    def add_to_history(self, command):
        """添加命令到历史记录"""
        if command and hasattr(self, 'session') and hasattr(self.session, 'history'):
            try:
                self.session.history.append_string(command)
            except Exception:
                pass  # 忽略添加历史记录失败的情况 