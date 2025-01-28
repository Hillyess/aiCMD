# 从原来的 command_translator.py 移动过来
class CommandTranslator:
    def __init__(self):
        self.command_map = {
            # 文件和目录操作
            'ls': 'dir',
            'pwd': 'cd',
            'rm': 'del',
            'rm -rf': 'rmdir /s /q',
            'cp': 'copy',
            'cp -r': 'xcopy /e /i',
            'mv': 'move',
            'mkdir -p': 'mkdir',
            'touch': 'type nul >',
            'cat': 'type',
            'head': 'more',
            'tail': 'more',
            'chmod': 'icacls',
            'chown': 'icacls',
            
            # 系统信息
            'uname': 'ver',
            'uname -a': 'systeminfo',
            'df': 'wmic logicaldisk get size,freespace,caption',
            'ps': 'tasklist',
            'ps aux': 'tasklist /v',
            'top': 'taskmgr',
            'kill': 'taskkill /PID',
            'killall': 'taskkill /IM',
            
            # 其他
            'clear': 'cls',
            'which': 'where',
            'echo': 'echo'
        }
        
        self.arg_map = {
            '-r': '/s',
            '-f': '/f',
            '-v': '/v',
            '-p': '',
            '-a': '/a',
            '-l': ''
        }

    def to_windows(self, linux_command):
        """将 Linux 命令转换为 Windows 命令"""
        return self.translate_command(linux_command)
        
    def to_linux(self, windows_command):
        """将 Windows 命令转换为 Linux 命令
        目前主要用于反向查找，确保命令存在对应关系
        """
        # 查找是否有对应的 Linux 命令
        win_cmd = windows_command.strip().split()[0].lower()
        for linux_cmd, mapped_cmd in self.command_map.items():
            if mapped_cmd.split()[0].lower() == win_cmd:
                return linux_cmd
        return windows_command

    def translate_command(self, linux_command):
        """转换命令（保持向后兼容）"""
        try:
            parts = linux_command.strip().split()
            if not parts:
                return linux_command
                
            cmd = parts[0].strip()
            args = parts[1:] if len(parts) > 1 else []
            
            if len(args) > 0:
                compound_cmd = f"{cmd} {args[0]}"
                if compound_cmd in self.command_map:
                    win_cmd = self.command_map[compound_cmd]
                    args = args[1:]
                else:
                    win_cmd = self.command_map.get(cmd, cmd)
            else:
                win_cmd = self.command_map.get(cmd, cmd)
            
            win_args = []
            for arg in args:
                arg = arg.strip()
                if arg.startswith('-'):
                    win_arg = self.arg_map.get(arg, arg)
                    if win_arg:
                        win_args.append(win_arg)
                else:
                    win_args.append(arg)
            
            final_cmd = f"{win_cmd} {' '.join(win_args)}" if win_args else win_cmd
            return final_cmd
            
        except Exception as e:
            print(f"命令转换错误: {str(e)}")
            return linux_command

    def is_linux_command(self, command):
        """检查是否是 Linux 命令"""
        cmd = command.strip().split()[0]
        return cmd in self.command_map 