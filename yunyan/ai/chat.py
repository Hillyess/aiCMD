import openai
import json
import os
import time
import threading
from ..utils.timer import ThinkingTimer

class ChatManager:
    """AI 对话管理"""
    def __init__(self, api_key=None):
        self.setup_client(api_key)
        self.conversation_history = []
        self.system_prompt = """你是云衍(YunYan)，一个专注于运维的AI助手。
当用户询问如何执行某个操作时：
1. 优先考虑命令行解决方案
2. 分析历史命令和输出，给出针对性建议
3. 确保建议的命令适用于用户的系统
4. 对于复杂任务，逐步给出命令
5. 关注运维安全，提醒潜在风险
6. 如果任务已完成，明确告知用户"""
        
    def setup_client(self, api_key=None):
        """设置 OpenAI 客户端"""
        default_api_key = "sk-be29fe8884b247eaa01665aa2dd21139"
        api_key = api_key or os.getenv('OPENAI_API_KEY', default_api_key)
        self.client = openai.Client(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

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
            stream = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    if not response:  # 第一个响应时停止计时
                        timer.stop()
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    response += content
            
            print()
            return response
            
        except Exception as e:
            timer.stop()
            error_msg = str(e)
            if "404" in error_msg:
                return "API 连接错误：无法连接到服务器。请检查网络连接或联系管理员。"
            return f"获取 AI 响应时出错: {error_msg}"
        finally:
            timer.stop() 