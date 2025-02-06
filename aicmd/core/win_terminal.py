import os
import sys
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from colorama import init, Fore, Style
from ..utils.emoji import EmojiSupport
import time

# 初始化 colorama 以支持 Windows 彩色输出
init()

class WindowsTerminal:
    """Windows 专用终端实现"""
    def __init__(self, callback=None):
        self.emoji = EmojiSupport()
        self.callback = callback
        self.thinking_time = None
        
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
                
            def get_completions(self, document, complete_event):
                word = document.get_word_before_cursor()
                text_before_cursor = document.text_before_cursor
                
                # 先检查是否是历史命令补全
                if word and not text_before_cursor.startswith(('cd ', 'dir ')):
                    # 从会话历史记录中查找匹配的命令
                    history = self.session.history.get_strings()
                    for cmd in reversed(history):  # 倒序遍历，最新的命令优先
                        if cmd.startswith(word):
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
        """创建 Windows 样式"""
        return PromptStyle.from_dict({
            'username': 'ansigreen bold',
            'hostname': 'ansigreen bold',
            'path': 'ansiblue bold',
            'prompt': 'ansiwhite',
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
            result = subprocess.run(
                f'cmd /c {command}',
                capture_output=True,
                text=True,
                encoding='gbk',  # 使用 GBK 编码
                errors='replace'
            )
            return result.stdout + result.stderr
        except Exception as e:
            return str(e)

    def get_prompt(self):
        """生成 Windows 风格提示符"""
        # 获取基本信息
        conda_env = os.environ.get('CONDA_DEFAULT_ENV', '')
        username = os.environ.get('USERNAME', '')
        hostname = os.environ.get('COMPUTERNAME', '')
        cwd = os.getcwd().replace('/', '\\')
        
        # 构建提示符
        prompt = []
        
        if self.thinking_time is not None:
            prompt.append(('class:default', f"({self.thinking_time:.1f}s) "))
        
        prompt.append(('class:default', f"{self.emoji.get('🤖')} "))
        
        if conda_env:
            prompt.append(('class:default', f"({conda_env}) "))
        
        prompt.extend([
            ('class:username', username),
            ('class:default', '@'),
            ('class:hostname', hostname),
            ('class:default', ':'),
            ('class:path', cwd),
            ('class:prompt', '$ ')
        ])
        
        return FormattedText(prompt)

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
                            full_query = f"""
上下文信息：
{context}

用户问题：
{query}
"""
                            response = self.callback(full_query)
                            self.chat_history.append((query, response))
                    else:
                        if command.startswith('cd '):
                            path = command[3:].strip()
                            try:
                                os.chdir(os.path.expanduser(path))
                                self.output_history.append("")
                            except Exception as e:
                                error = f"错误: {str(e)}"
                                print(f"{Fore.RED}{error}{Style.RESET_ALL}")
                                self.output_history.append(error)
                        else:
                            output = self._capture_output(command)
                            self.output_history.append(output)
                            print(output, end='')
                            
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
        print("\n=== 云衍 (YunYan) 智能运维助手 ===")
        print(f"{self.emoji.get('👋')} 欢迎使用云衍！")
        print(f"{self.emoji.get('💡')} 输入 / 开头的内容可以询问 AI")
        print(f"{self.emoji.get('💻')} 输入 'exit' 退出程序")
        print("示例：/如何查看系统状态")
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