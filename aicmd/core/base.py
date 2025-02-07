class BaseTerminal:
    """终端基类"""
    def __init__(self, callback=None, agent_mode=False):
        self.callback = callback
        self.command_history = []
        self.output_history = []
        self.chat_history = []
        self.agent_mode = agent_mode
        self.emoji = {
            '👋': '👋',
            '💡': '💡',
            '💻': '💻',
            '🤖': '🤖',  # 基础机器人
            '🤖️️️Q': '🤖️️️Q',  # 问答模式
            '🤖️️️A': '🤖️️️A',  # Agent模式
        } 