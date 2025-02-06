import requests
import json
import os
import time
import threading
from ..utils.timer import ThinkingTimer
from ..config.settings import Settings

class ChatManager:
    """AI 对话管理"""
    def __init__(self, api_key=None):
        self.setup_client(api_key)
        self.conversation_history = []
        self.system_prompt = """你是 aiCMD，一个专注于运维的AI助手。
当用户询问如何执行某个操作时：
1. 优先考虑命令行解决方案
2. 分析历史命令和输出，给出针对性建议
3. 确保建议的命令适用于用户的系统
4. 对于复杂任务，逐步给出命令
5. 关注运维安全，提醒潜在风险
6. 如果任务已完成，明确告知用户"""
        
    def setup_client(self, api_key=None):
        """设置 API 配置"""
        settings = Settings()
        
        # 检查配置
        if not settings.check_api_config():
            if not settings.setup_wizard():
                raise Exception("API 配置失败")
        
        # 保存 API 信息
        self.api_key = settings.get('api.key')
        self.base_url = settings.get('api.base_url')

    def get_response(self, query, system_info, context=""):
        """获取 AI 响应"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"系统信息：\n{json.dumps(system_info, ensure_ascii=False, indent=2)}"},
            {"role": "user", "content": f"历史记录：\n{context}\n当前问题：{query}"}
        ]

        timer = ThinkingTimer("AI 思考中")
        timer.start()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": messages,
                "stream": True
            }
            
            response = requests.request(
                "POST",
                self.base_url,
                json=payload,
                headers=headers,
                stream=True
            )
            
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        if line == 'data: [DONE]':
                            break
                        
                        try:
                            data = json.loads(line[6:])  # 跳过 'data: ' 前缀
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    if content:  # 只处理非空内容
                                        if not full_response:  # 第一个响应时停止计时
                                            timer.stop()
                                        print(content, end='', flush=True)
                                        full_response += content
                        except json.JSONDecodeError:
                            continue
            
            print()
            return full_response
            
        except Exception as e:
            timer.stop()
            error_msg = str(e)
            if "401" in error_msg:
                return "API Key 无效或未授权。请检查你的 API Key。"
            elif "404" in error_msg:
                return "API 连接错误：无法连接到服务器。请检查网络连接或联系管理员。"
            return f"获取 AI 响应时出错: {error_msg}"
        finally:
            timer.stop() 