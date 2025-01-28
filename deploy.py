import os
import sys
import subprocess
import argparse
import tempfile
import shutil
import time

# 默认配置
DEFAULT_HOST = "ubuntu@101.43.199.111"
DEFAULT_PATH = "/home/ubuntu/code/AutoCloud"
TIMEOUT = 10  # 设置超时时间（秒）

def ensure_remote_dir(host, path):
    """确保远程目录存在"""
    try:
        print(f"检查并创建远程目录: {path}")
        mkdir_cmd = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',  # SSH 连接超时
            '-o', 'BatchMode=yes',      # 禁用交互式提示
            '-i', os.path.expanduser('~/.ssh/id_rsa'),
            host,
            f'mkdir -p {path}'
        ]
        
        # 使用超时运行命令
        process = subprocess.Popen(
            mkdir_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT)
            if process.returncode != 0:
                print(f"创建目录失败: {stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            process.kill()
            print("创建目录超时")
            return False
            
    except Exception as e:
        print(f"创建远程目录失败: {e}")
        return False

def deploy_to_ecs(host=DEFAULT_HOST, remote_path=DEFAULT_PATH):
    """部署代码到 ECS 服务器"""
    try:
        # 首先确保远程目录存在
        if not ensure_remote_dir(host, remote_path):
            print("无法创建远程目录，部署终止")
            sys.exit(1)
            
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 复制项目文件到临时目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            for item in os.listdir(current_dir):
                if item not in ['.git', '__pycache__', 'build', 'dist']:
                    src = os.path.join(current_dir, item)
                    dst = os.path.join(temp_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # 使用 scp 命令，指定使用密钥认证
            scp_cmd = [
                'scp',
                '-r',  # 递归复制目录
                '-o', 'StrictHostKeyChecking=no',  # 自动接受服务器指纹
                '-o', 'ConnectTimeout=10',         # 连接超时
                '-o', 'BatchMode=yes',            # 禁用交互式提示
                '-o', 'PasswordAuthentication=no', # 禁用密码认证
                '-i', os.path.expanduser('~/.ssh/id_rsa'),  # 指定私钥
                f'{temp_dir}/*',
                f'{host}:{remote_path}'
            ]
            
            print(f"正在部署到 {host}:{remote_path}")
            process = subprocess.Popen(
                scp_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=TIMEOUT)
                if process.returncode != 0:
                    print(f"部署失败: {stderr}")
                    sys.exit(1)
                print("部署成功！")
            except subprocess.TimeoutExpired:
                process.kill()
                print("部署超时")
                sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n部署被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='部署代码到 ECS 服务器')
    parser.add_argument('--host', default=DEFAULT_HOST, help='服务器地址')
    parser.add_argument('--path', default=DEFAULT_PATH, help='远程服务器上的目标路径')
    args = parser.parse_args()
    
    deploy_to_ecs(args.host, args.path) 