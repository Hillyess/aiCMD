import subprocess
import os
import sys
from ..utils.translator import CommandTranslator

class CommandExecutor:
    """命令执行器"""
    def __init__(self):
        self.translator = CommandTranslator()
        self.internal_commands = {'dir', 'cd', 'type', 'copy', 'move', 'del', 'rd', 'md', 'cls', 'echo'}
        self.parser = CommandParser()
        
        # ANSI 颜色代码
        self.colors = {
            'dir': '\033[1;34m',    # 亮蓝色
            'exe': '\033[1;32m',    # 亮绿色
            'link': '\033[1;36m',   # 亮青色
            'file': '\033[0;37m',   # 白色
            'reset': '\033[0m'      # 重置
        }
    
    def _colorize_output(self, output, command):
        """为输出添加颜色"""
        if not output:
            return output
            
        # 处理 ls 和 dir 命令的输出
        if command.strip().startswith(('ls', 'dir')):
            lines = output.splitlines()
            colored_lines = []
            
            # 启用 Windows 的 ANSI 支持
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            
            for line in lines:
                # 跳过空行
                if not line.strip():
                    colored_lines.append(line)
                    continue
                    
                # Linux 下的 ls 输出格式处理
                if os.name != 'nt':
                    parts = line.split()
                    if not parts:
                        continue
                        
                    # 处理长格式（ls -l）输出
                    if line[0] in 'dl-':
                        if line.startswith('d'):  # 目录
                            colored_lines.append(f"{self.colors['dir']}{line}{self.colors['reset']}")
                        elif 'x' in parts[0]:  # 可执行文件
                            colored_lines.append(f"{self.colors['exe']}{line}{self.colors['reset']}")
                        elif line.startswith('l'):  # 符号链接
                            colored_lines.append(f"{self.colors['link']}{line}{self.colors['reset']}")
                        else:  # 普通文件
                            colored_lines.append(f"{self.colors['file']}{line}{self.colors['reset']}")
                    # 处理简单格式（ls）输出
                    else:
                        filename = line
                        path = os.path.join(os.getcwd(), filename)
                        if os.path.exists(path):
                            if os.path.isdir(path):  # 目录
                                colored_lines.append(f"{self.colors['dir']}{filename}{self.colors['reset']}")
                            elif os.access(path, os.X_OK):  # 可执行文件
                                colored_lines.append(f"{self.colors['exe']}{filename}{self.colors['reset']}")
                            elif os.path.islink(path):  # 符号链接
                                colored_lines.append(f"{self.colors['link']}{filename}{self.colors['reset']}")
                            else:  # 普通文件
                                colored_lines.append(f"{self.colors['file']}{filename}{self.colors['reset']}")
                        else:
                            colored_lines.append(f"{self.colors['file']}{filename}{self.colors['reset']}")
                else:
                    # Windows 的 dir 输出格式处理
                    if '<DIR>' in line:  # 目录
                        colored_lines.append(f"{self.colors['dir']}{line}{self.colors['reset']}")
                    elif any(line.lower().endswith(ext) for ext in ('.exe', '.bat', '.cmd', '.sh')):  # 可执行文件
                        colored_lines.append(f"{self.colors['exe']}{line}{self.colors['reset']}")
                    else:  # 普通文件
                        colored_lines.append(f"{self.colors['file']}{line}{self.colors['reset']}")
            
            return '\n'.join(colored_lines)
        return output

    def execute(self, command):
        """执行命令"""
        try:
            # 首先解析命令
            parsed_cmd = self.parser.parse(command)
            if not parsed_cmd:
                return "无效的命令", "命令解析失败"

            # 获取命令和参数
            cmd_parts = parsed_cmd.strip().split()
            cmd = cmd_parts[0]
            args = cmd_parts[1:] if len(cmd_parts) > 1 else []

            # 特殊处理 cd 命令
            if cmd in ['cd']:
                return self._handle_cd(args)

            # 检查是否是 Linux 命令需要转换
            if self.translator.is_linux_command(parsed_cmd):
                parsed_cmd = self.translator.to_windows(parsed_cmd)
            
            # 执行命令
            if os.name == 'nt' and parsed_cmd.split()[0] in self.internal_commands:
                stdout, stderr = self._execute_windows_internal(parsed_cmd)
            else:
                stdout, stderr = self._execute_shell(parsed_cmd)
                
            # 为输出添加颜色
            if stdout and cmd in ['ls', 'dir']:
                stdout = self._colorize_output(stdout, cmd)
            
            return stdout, stderr
                
        except Exception as e:
            return "", f"命令执行错误: {str(e)}"

    def _handle_cd(self, args):
        """处理 cd 命令"""
        try:
            # 没有参数时显示当前目录
            if not args:
                return os.getcwd(), ""
            
            # 处理目标路径
            path = args[0]
            if path == '-':
                # cd - 返回上一个目录
                if hasattr(self, '_last_dir'):
                    path = self._last_dir
                else:
                    return "", "没有上一个目录"
            
            # 保存当前目录
            self._last_dir = os.getcwd()
            
            # 改变目录
            os.chdir(os.path.expanduser(path))
            return "", ""
            
        except Exception as e:
            return "", f"cd: {str(e)}"

    def _execute_windows_internal(self, command):
        """Windows 内部命令执行"""
        try:
            # Windows 内部命令需要通过 cmd /c 执行，但要正确处理命令字符串
            cmd_parts = ['cmd', '/c']
            # 将命令拆分为列表形式，避免引号问题
            if isinstance(command, str):
                command_parts = command.split()
            else:
                command_parts = command
            cmd_parts.extend(command_parts)
            
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False  # 使用 shell=False，但通过 cmd /c 执行
            )
            stdout, stderr = process.communicate()
            return stdout, stderr
        except Exception as e:
            return "", f"命令执行错误: {str(e)}"

    def _execute_shell(self, command):
        """Unix 命令执行"""
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=dict(os.environ, LANG='en_US.UTF-8')  # 确保正确的字符编码
        )
        stdout, stderr = process.communicate()
        return stdout, stderr

class CommandParser:
    """命令解析器"""
    def __init__(self):
        self.special_chars = {'"', "'", '|', '>', '<', '&', ';'}
    
    def parse(self, command):
        """解析命令
        
        Args:
            command: 要解析的命令字符串
            
        Returns:
            str: 处理后的命令，如果命令无效则返回 None
        """
        if not command:
            return None
            
        command = command.strip()
        
        # 检查危险命令
        if self._is_dangerous(command):
            return None
            
        # 处理引号和转义字符
        command = self._handle_quotes(command)
        
        return command
    
    def _is_dangerous(self, command):
        """检查是否是危险命令"""
        dangerous_commands = {
            'rm -rf /',
            'rm -rf *',
            'format',
            'mkfs',
            ':(){:|:&};:',  # fork 炸弹
            '> /dev/sda',
            'dd if=/dev/zero'
        }
        
        cmd_lower = command.lower()
        return any(dc in cmd_lower for dc in dangerous_commands)
    
    def _handle_quotes(self, command):
        """处理命令中的引号"""
        result = []
        in_quotes = False
        quote_char = None
        escaped = False
        
        for char in command:
            if escaped:
                result.append(char)
                escaped = False
                continue
                
            if char == '\\':
                escaped = True
                continue
                
            if char in {'"', "'"}:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                result.append(char)
                continue
                
            if not in_quotes and char in self.special_chars:
                # 处理特殊字符
                result.append(f' {char} ')
            else:
                result.append(char)
                
        return ''.join(result) 