import os
import sys
import json
import platform
import time
from .terminal import Terminal
from .command import CommandExecutor
from ..ai.chat import ChatManager
from ..ai.search import SearchEngine

class Assistant:
    """aiCMD主控制器"""
    def __init__(self, agent_mode=False):
        try:
            self.agent_mode = agent_mode
            # 初始化各个组件
            self.terminal = Terminal(callback=self.handle_ai_query)
            self.executor = CommandExecutor()
            self.chat = ChatManager()
            self.search = SearchEngine()
            
            # 历史记录
            self.command_history = []
            self.context = []
            
            # 系统信息
            self.environment_info = self.collect_system_info()
            
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            raise

    def run(self):
        """运行主循环"""
        try:
            # 直接运行终端，不再需要创建会话
            self.terminal.run()
        except KeyboardInterrupt:
            print(f"\n{self.terminal.emoji.get('👋')} 再见！")
            sys.exit(0)
        except Exception as e:
            print(f"运行时错误: {str(e)}")
            sys.exit(1)

    def handle_input(self, text):
        """处理用户输入"""
        # 记录用户输入
        self.command_history.append(text)
        
        # 检查是否是 AI 查询
        if text.startswith('/') or self.is_chinese(text[0]):
            query = text[1:] if text.startswith('/') else text
            self.handle_ai_query(query)
        else:
            # 执行命令
            stdout, stderr = self.executor.execute(text)
            
            # 保存命令执行结果
            self.context.append({
                "command": text,
                "output": stdout,
                "error": stderr
            })
            
            # 显示输出
            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)

    def handle_ai_query(self, query):
        """处理 AI 查询"""
        try:
            context = self._build_full_context()
            
            if self.agent_mode:
                query = f"[AGENT_MODE] {query}"
            
            response = self.chat.get_response(
                query,
                self.environment_info,
                context
            )
            
            self.context.append(f"用户: {query}")
            self.context.append(f"AI: {response}")
            
            if self.agent_mode and '```' in response:
                command = self.extract_command(response)
                if command:
                    print(f"\nAI 建议执行命令：{command}")
                    
                    if 'Set-ExecutionPolicy' in command or 'chocolatey' in command.lower():
                        print("\n⚠️ 注意：此命令需要在管理员权限的 PowerShell 中执行")
                        print("请打开管理员权限的 PowerShell 并复制命令执行")
                        if hasattr(self.terminal, 'add_to_history'):
                            self.terminal.add_to_history(command)
                        return
                    
                    print("提示：按↑键获取命令，按回车执行")
                    
                    # 将命令添加到历史记录并预输入
                    if hasattr(self.terminal, 'session'):
                        try:
                            # 添加到历史记录
                            self.terminal.add_to_history(command)
                            
                            # 获取当前应用实例
                            app = self.terminal.session.app
                            
                            # 在主线程中更新缓冲区
                            def update_buffer():
                                app.current_buffer.text = command
                                app.current_buffer.cursor_position = len(command)
                            
                            # 如果应用正在运行，使用 call_from_executor
                            if app.is_running:
                                app.loop.call_soon_threadsafe(update_buffer)
                            
                        except Exception as e:
                            print(f"\n预输入命令失败: {e}")
                            print(f"你可以手动复制命令：{command}")
            else:
                if '```' in response:
                    command = self.extract_command(response)
                    if command:
                        print(f"\nAI 建议的命令：{command}")
                        print("提示：你可以直接复制此命令或使用上箭头键获取此命令")
                        if hasattr(self.terminal, 'add_to_history'):
                            self.terminal.add_to_history(command)
                            
        except Exception as e:
            print(f"AI 查询失败: {str(e)}")

    def _build_full_context(self):
        """构建完整的历史上下文"""
        context_parts = []
        
        # 添加命令历史和执行结果
        if self.context:
            context_parts.append("历史命令和执行结果：")
            for item in self.context[-10:]:  # 保留最近10条记录
                if isinstance(item, dict):
                    # 命令执行记录
                    context_parts.append(f"执行命令: {item['command']}")
                    if item['output']:
                        context_parts.append(f"命令输出:\n{item['output']}")
                    if item['error']:
                        context_parts.append(f"错误信息:\n{item['error']}")
                else:
                    # 对话记录
                    context_parts.append(item)
                context_parts.append("---")
        
        return "\n".join(context_parts)

    def build_context(self):
        """构建上下文信息"""
        context_parts = []
        
        # 添加命令历史
        if self.context:
            context_parts.append("命令执行历史：")
            for ctx in self.context[-5:]:  # 只保留最近5条记录
                context_parts.append(f"命令: {ctx['command']}")
                if ctx['output']:
                    context_parts.append(f"输出: {ctx['output']}")
                if ctx['error']:
                    context_parts.append(f"错误: {ctx['error']}")
                context_parts.append("---")
        
        return "\n".join(context_parts)

    def collect_system_info(self):
        """收集系统信息"""
        info = {
            'os': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine()
            },
            'env': {
                'PATH': os.environ.get('PATH', ''),
                'PYTHON_VERSION': sys.version,
                'CONDA_PREFIX': os.environ.get('CONDA_PREFIX', '')
            },
            'shell': self._detect_shell()
        }
        return info
        
    def _detect_shell(self):
        """检测当前使用的 shell"""
        try:
            if platform.system() == 'Windows':
                # 检查 Windows 终端类型
                if 'PROMPT' in os.environ:  # CMD
                    return {
                        'type': 'cmd',
                        'version': os.environ.get('COMSPEC', ''),
                        'prompt': os.environ.get('PROMPT', '')
                    }
                elif 'PSModulePath' in os.environ:  # PowerShell
                    import subprocess
                    try:
                        version = subprocess.check_output(['powershell', '$PSVersionTable.PSVersion']).decode()
                        return {
                            'type': 'powershell',
                            'version': version.strip(),
                            'profile': os.environ.get('PSExecutionPolicyPreference', '')
                        }
                    except:
                        return {
                            'type': 'powershell',
                            'version': 'unknown'
                        }
                else:
                    return {
                        'type': 'unknown_windows_shell'
                    }
            else:
                # Unix-like 系统
                shell_path = os.environ.get('SHELL', '')
                shell_type = os.path.basename(shell_path)
                
                # 获取 shell 版本
                version = ''
                try:
                    if shell_type == 'bash':
                        version = subprocess.check_output([shell_path, '--version']).decode().split('\n')[0]
                    elif shell_type == 'zsh':
                        version = subprocess.check_output([shell_path, '--version']).decode().strip()
                    elif shell_type == 'fish':
                        version = subprocess.check_output([shell_path, '--version']).decode().strip()
                except:
                    pass
                
                return {
                    'type': shell_type,
                    'path': shell_path,
                    'version': version,
                    'rc_file': self._get_shell_rc_file(shell_type)
                }
        except Exception as e:
            return {
                'type': 'unknown',
                'error': str(e)
            }
            
    def _get_shell_rc_file(self, shell_type):
        """获取 shell 的配置文件路径"""
        home = os.path.expanduser('~')
        if shell_type == 'bash':
            return os.path.join(home, '.bashrc')
        elif shell_type == 'zsh':
            return os.path.join(home, '.zshrc')
        elif shell_type == 'fish':
            return os.path.join(home, '.config/fish/config.fish')
        return ''

    @staticmethod
    def extract_command(response):
        """从 AI 响应中提取命令"""
        try:
            # 查找代码块
            start_markers = ['```command', '```']
            start = -1
            for marker in start_markers:
                pos = response.find(marker)
                if pos != -1:
                    start = pos + len(marker)
                    break
                    
            if start == -1:
                return None
                
            # 找到代码块结束位置
            end = response.find('```', start)
            if end == -1:
                return None
                
            # 提取命令内容
            command_block = response[start:end].strip()
            
            # 处理命令块
            lines = command_block.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # 检查是否是环境标记行
                if line.lower() in ['bash', 'powershell', 'cmd', 'sh', 'zsh', 'fish']:
                    continue
                    
                # 检查是否包含环境标记
                if ' ' in line:  # 如果行内包含空格
                    parts = line.split()
                    if parts[0].lower() in ['bash', 'powershell', 'cmd', 'sh', 'zsh', 'fish']:
                        continue
                        
                return line  # 返回第一个有效命令
                
            return None
            
        except Exception:
            return None

    @staticmethod
    def is_chinese(char):
        """检查字符是否是中文"""
        return '\u4e00' <= char <= '\u9fff' 