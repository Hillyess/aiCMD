import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from colorama import Fore, Style, init
from ..utils.emoji import EmojiSupport
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style as PromptStyle
import glob
import time
import platform
from .base import BaseTerminal  # 从 base.py 导入基类

# 初始化 colorama
init()

class SimpleCompleter(Completer):
    """简单的补全器实现"""
    def __init__(self, session):
        self.commands = self._get_commands()
        self.session = session  # 保存 session 引用
        self.completion_cache = set()  # 添加缓存集合
    
    def _get_commands(self):
        """获取系统命令"""
        commands = {'cd', 'ls', 'pwd', 'exit', 'help'}
        try:
            paths = os.environ.get('PATH', '').split(os.pathsep)
            for path in paths:
                if os.path.exists(path):
                    for item in os.listdir(path):
                        full_path = os.path.join(path, item)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            commands.add(item)
        except Exception as e:
            print(f"Warning: Error getting commands: {e}")
        return sorted(commands)
    
    def get_completions(self, document, complete_event):
        """获取补全项"""
        word = document.get_word_before_cursor()
        text_before_cursor = document.text_before_cursor
        
        # 先检查是否是历史命令补全
        if word and not text_before_cursor.startswith(('cd ', 'ls ')):
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
        if text_before_cursor.startswith('cd ') or text_before_cursor.startswith('ls '):
            # 路径补全
            cmd_parts = text_before_cursor.split(maxsplit=1)
            path = cmd_parts[1] if len(cmd_parts) > 1 else ''
            
            # 处理删除后的路径
            if '/' in path:
                # 获取最后一个 / 之前的路径作为基础目录
                base_path = path.rsplit('/', 1)[0]
                search_pattern = path.rsplit('/', 1)[1]
            else:
                base_path = ''
                search_pattern = path
            
            # 获取要补全的目录
            if base_path.startswith('~'):
                base_dir = os.path.expanduser(base_path)
            elif base_path.startswith('/'):
                base_dir = base_path
            elif base_path:
                base_dir = os.path.join(os.getcwd(), base_path)
            else:
                base_dir = os.getcwd()
            
            try:
                # 确保基础目录存在
                if not os.path.exists(base_dir):
                    base_dir = os.getcwd()
                
                # 列出目录内容
                items = os.listdir(base_dir)
                
                # 过滤和排序
                items = [
                    item for item in items
                    if item.startswith(search_pattern) and not item.startswith('.')
                ]
                
                # 先显示目录，再显示文件
                dirs = []
                files = []
                for item in sorted(items):
                    full_path = os.path.join(base_dir, item)
                    if os.path.isdir(full_path):
                        dirs.append((item, full_path))
                    else:
                        files.append((item, full_path))
                
                # 生成补全项
                for item, full_path in dirs + files:
                    display = item + ('/' if os.path.isdir(full_path) else '')
                    
                    # 计算补全文本
                    if base_path:
                        if base_path.startswith('/'):
                            completion = os.path.join(base_path, item)
                        elif base_path.startswith('~'):
                            completion = os.path.join(base_path, item)
                        else:
                            rel_path = os.path.relpath(full_path, os.getcwd())
                            completion = rel_path
                    else:
                        if path.startswith('/'):
                            completion = full_path
                        elif path.startswith('~'):
                            completion = os.path.join('~', item)
                        else:
                            completion = './' + item
                    
                    # 确保使用 Unix 风格路径
                    completion = completion.replace('\\', '/')
                    
                    # 确保目录以 / 结尾
                    if os.path.isdir(full_path) and not completion.endswith('/'):
                        completion += '/'
                    
                    yield Completion(
                        completion,
                        start_position=-len(path),
                        display=display,
                        display_meta='dir' if os.path.isdir(full_path) else 'file'
                    )
                    
            except Exception as e:
                pass
                
        else:
            # 命令补全
            for cmd in self.commands:
                if cmd.startswith(word):
                    yield Completion(
                        cmd,
                        start_position=-len(word)
                    )

class UnixTerminal(BaseTerminal):
    """Unix 终端实现"""
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
        self.completer = SimpleCompleter(self.session)
        
        # 设置补全器
        self.session.completer = self.completer
        
        # 创建输出捕获管道
        self.output_pipe = os.pipe() if hasattr(os, 'pipe') else None
        
        # 添加历史记录跟踪
        self.command_history = []
        self.output_history = []
        self.chat_history = []

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
                sys.exit(0)
            else:
                self.last_ctrl_c_time = current_time
                print('^C')
            
        @bindings.add('c-d')
        def _(event):
            """处理 Ctrl+D"""
            print(f"\n{self.emoji.get('👋')} 再见！")
            event.app.exit()
            sys.exit(0)
            
        @bindings.add('c-w')
        def _(event):
            """处理 Ctrl+W：删除光标前的一个词"""
            b = event.current_buffer
            pos = b.document.find_previous_word_beginning(count=1)
            if pos:
                deleted = b.delete_before_cursor(count=-pos)
                event.app.clipboard.set_data(deleted)  # 保存到剪贴板
            
        @bindings.add('c-u')
        def _(event):
            """处理 Ctrl+U：删除光标前的所有内容"""
            b = event.current_buffer
            deleted = b.delete_before_cursor(count=b.document.cursor_position)
            event.app.clipboard.set_data(deleted)  # 保存到剪贴板
            
        @bindings.add('c-left')
        def _(event):
            """处理 Ctrl+左箭头：向左移动一个词"""
            b = event.current_buffer
            pos = b.document.find_previous_word_beginning(count=1)
            if pos:
                b.cursor_position += pos
                
        @bindings.add('c-right')
        def _(event):
            """处理 Ctrl+右箭头：向右移动一个词"""
            b = event.current_buffer
            pos = b.document.find_next_word_ending()
            if pos:
                b.cursor_position += pos
                
        @bindings.add('c-h')  # 在 Linux 中，Ctrl+H 等同于 Backspace
        def _(event):
            """处理 Ctrl+H：删除前一个词"""
            b = event.current_buffer
            pos = b.document.find_previous_word_beginning(count=1)
            if pos:
                deleted = b.delete_before_cursor(count=-pos)
                event.app.clipboard.set_data(deleted)
            
        @bindings.add('tab')
        def _(event):
            """处理 Tab 键"""
            b = event.current_buffer
            if b.complete_state:
                b.complete_next()
            else:
                b.start_completion(select_first=False)

        @bindings.add('right')
        def _(event):
            """处理右箭头键"""
            b = event.current_buffer
            if b.complete_state and b.complete_state.current_completion:
                completion = b.complete_state.current_completion
                b.apply_completion(completion)
                
                # 如果是目录，立即开始新的补全
                if completion.text.endswith('/'):
                    b.start_completion(select_first=False)
                else:
                    b.complete_state = None

        @bindings.add('space')
        def _(event):
            """处理空格键"""
            b = event.current_buffer
            if b.complete_state and b.complete_state.current_completion:
                # 在补全状态下
                completion = b.complete_state.current_completion
                b.apply_completion(completion)
                
                # 如果是目录，立即开始新的补全
                if completion.text.endswith('/'):
                    b.start_completion(select_first=False)
                else:
                    b.insert_text(' ')
                    b.complete_state = None
            else:
                # 不在补全状态下，直接插入空格
                b.insert_text(' ')
            
        return bindings

    def _create_style(self):
        """创建提示符样式"""
        return PromptStyle.from_dict({
            'ansiyellow': 'ansibrightyellow bold',
            'ansiblue': 'ansibrightblue bold',
            'prompt': 'ansiwhite',
            'ai': 'ansibrightmagenta bold'
        })

    def get_prompt(self):
        """获取命令提示符"""
        # 根据模式选择不同的机器人表情
        if hasattr(self, 'agent_mode') and self.agent_mode:
            robot = self.emoji.get('️A')  # Agent模式
        else:
            robot = self.emoji.get('Q')  # 问答模式
            
        # 获取基本信息
        username = os.getlogin()
        hostname = platform.node()
        cwd = os.getcwd()
        
        # 使用 FormattedText 构建提示符
        return FormattedText([
            ('', f'{robot} '),  # 机器人表情
            ('', '(ai) '),  # 固定标识
            ('class:ansiyellow', f'{username}@{hostname}'),  # 用户名和主机名（黄色）
            ('', ':'),
            ('class:ansiblue', cwd),  # 当前目录（蓝色）
            ('class:prompt', ' $ ')  # 提示符
        ])

    def _capture_output(self, command):
        """捕获命令输出"""
        if not self.output_pipe:
            # 如果不支持 pipe，直接执行
            return os.popen(command).read()
            
        # 保存原始文件描述符
        stdout_fd = os.dup(1)
        stderr_fd = os.dup(2)
        
        # 重定向输出到管道
        os.dup2(self.output_pipe[1], 1)
        os.dup2(self.output_pipe[1], 2)
        
        try:
            # 执行命令
            os.system(command)
            
            # 刷新输出
            sys.stdout.flush()
            sys.stderr.flush()
            
            # 读取输出
            os.close(self.output_pipe[1])
            output = os.read(self.output_pipe[0], 65536).decode('utf-8', errors='replace')
            
            # 创建新的管道
            self.output_pipe = os.pipe()
            
            return output
            
        finally:
            # 恢复原始文件描述符
            os.dup2(stdout_fd, 1)
            os.dup2(stderr_fd, 2)
            os.close(stdout_fd)
            os.close(stderr_fd)

    def _build_context(self):
        """构建上下文信息"""
        context = []
        
        # 添加系统信息
        context.append("=== 系统环境 ===")
        context.append(f"当前目录: {os.getcwd()}")
        context.append(f"Python版本: {sys.version.split()[0]}")
        context.append("")
        
        # 添加最近的命令历史和输出
        context.append("=== 最近操作 ===")
        for i, (cmd, output) in enumerate(zip(self.command_history[-5:], self.output_history[-5:])):
            context.append(f"命令[{i+1}]: {cmd}")
            if output.strip():
                context.append(f"输出[{i+1}]:\n{output.strip()}")
            context.append("")
        
        # 添加聊天历史
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
                        self.get_prompt(),
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

    def _get_shortened_path(self, path):
        """获取简化的路径"""
        home = os.path.expanduser('~')
        if path.startswith(home):
            return '~' + path[len(home):]
        return path

    def show_welcome(self):
        """显示欢迎信息"""
        print(f"\n=== {Fore.CYAN}aiCMD智能运维助手{Style.RESET_ALL} ===")
        print(f"{self.emoji.get('👋')} 欢迎使用aiCMD！")
        if self.agent_mode:
            print(f"{self.emoji.get('🤖')} {Fore.GREEN}已进入 Agent 模式{Style.RESET_ALL}")
            print(f"{self.emoji.get('💡')} 直接描述你想完成的任务即可")
            print(f"示例：{Fore.CYAN}安装并配置 Nginx 服务器{Style.RESET_ALL}")
        else:
            print(f"{self.emoji.get('💡')} 输入 / 开头的内容可以询问 AI")
            print(f"{self.emoji.get('💻')} 输入 'exit' 退出程序")
            print(f"示例：{Fore.CYAN}/如何查看系统状态{Style.RESET_ALL}")
        print("=====================\n")

    def set_thinking_time(self, time):
        """设置思考时间"""
        self.thinking_time = time

    def add_to_history(self, command):
        """添加命令到历史记录"""
        if command:
            self.session.history.append_string(command) 

class Terminal(BaseTerminal):
    """终端工厂类"""
    def __new__(cls, callback=None, agent_mode=False):
        if os.name == 'nt':
            from .win_terminal import WindowsTerminal
            return WindowsTerminal(callback, agent_mode)
        else:
            return UnixTerminal(callback, agent_mode)

    def __init__(self, callback=None, agent_mode=False):
        """初始化终端"""
        super().__init__(callback, agent_mode)
        self.callback = callback
        self.agent_mode = agent_mode 