import json
import time
from openai import OpenAI
from ..utils.timer import ThinkingTimer
from ..config.settings import Settings
import sys
from ..prompts.base import SYSTEM_PROMPT, WINDOWS_SHELL_CHECK, COMMAND_ANALYSIS

class ChatManager:
    """AI 对话管理"""
    def __init__(self, api_key=None):
        self.setup_client(api_key)
        self.conversation_history = []
        self.system_prompt = SYSTEM_PROMPT
        
    def setup_client(self, api_key=None):
        """设置 API 客户端"""
        settings = Settings()
        
        # 检查配置
        if not settings.check_api_config():
            if not settings.setup_wizard():
                raise Exception("API 配置失败")
        
        # 创建 OpenAI 客户端
        self.client = OpenAI(
            base_url='http://localhost:11434/v1/',
            api_key='ollama',  # required but ignored
        )

    def get_response(self, query, system_info, context=""):
        """获取 AI 响应"""
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "system",
                "content": f"系统信息：\n{json.dumps(system_info, ensure_ascii=False, indent=2)}"
            },
            {
                "role": "user",
                "content": f"历史记录：\n{context}\n当前问题：{query}"
            }
        ]

        timer = ThinkingTimer("AI 思考中")
        timer.start()

        try:
            # 创建聊天完成
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model='deepseek-r1:14b',
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )
            
            full_response = ""
            is_thinking = False  # 标记是否在思考模式
            thinking_buffer = ""  # 用于缓存思考内容
            
            for chunk in chat_completion:
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        if not full_response:  # 第一个响应时停止计时
                            timer.stop()
                            
                        # 检查是否进入思考模式
                        if '<think>' in content:
                            is_thinking = True
                            # 只保留 <think> 之前的内容
                            before_think = content.split('<think>')[0]
                            if before_think:
                                print(before_think, end='', flush=True)
                                full_response += before_think
                            continue
                            
                        # 检查是否退出思考模式
                        if '</think>' in content:
                            is_thinking = False
                            # 只保留 </think> 之后的内容
                            after_think = content.split('</think>')[1]
                            if after_think:
                                print(after_think, end='', flush=True)
                                full_response += after_think
                            continue
                            
                        # 根据是否在思考模式决定是否输出
                        if not is_thinking:
                            print(content, end='', flush=True)
                            full_response += content
                        else:
                            thinking_buffer += content  # 缓存思考内容
            
            if not full_response:
                return "AI 没有返回有效响应。"
                
            print()  # 确保最后有换行
            return full_response
            
        except Exception as e:
            timer.stop()
            error_msg = str(e)
            if "Connection refused" in error_msg:
                return "无法连接到 Ollama 服务。请确保 Ollama 正在运行。"
            return f"获取 AI 响应时出错: {error_msg}"
        finally:
            timer.stop() 