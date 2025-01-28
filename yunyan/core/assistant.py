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
    """云衍主控制器"""
    def __init__(self):
        try:
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
            # 记录上下文
            context = "\n".join(self.context[-5:])  # 保留最近5条记录
            
            # 获取 AI 响应
            response = self.chat.get_response(
                query,
                self.environment_info,
                context
            )
            
            # 更新上下文
            self.context.append(f"用户: {query}")
            self.context.append(f"AI: {response}")
            
            # 提取可能的命令
            if '```' in response:
                command = self.extract_command(response)
                if command:
                    print(f"\nAI 建议的命令：{command}")
                    print("提示：你可以直接复制此命令或使用上箭头键获取此命令")
                    # 添加到终端历史记录
                    self.terminal.add_to_history(command)
        except Exception as e:
            print(f"AI 查询失败: {str(e)}")

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
            }
        }
        return info

    @staticmethod
    def extract_command(response):
        """从 AI 响应中提取命令"""
        try:
            start = response.find('```') + 3
            end = response.find('```', start)
            if start > 2 and end != -1:
                command = response[start:end].strip()
                if '\n' in command:
                    command = command.split('\n', 1)[1]
                return command.strip()
            return None
        except Exception:
            return None

    @staticmethod
    def is_chinese(char):
        """检查字符是否是中文"""
        return '\u4e00' <= char <= '\u9fff' 