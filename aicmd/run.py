from .core import Assistant
import sys

def main():
    try:
        print("\n=== aiCMD - AI-Powered Command-Line Assistant ===")
        print("请选择运行模式：")
        print("1. 问答模式 (直接回车)")
        print("2. Agent 模式 (输入 a)")
        
        mode = input("请选择 [回车/a]: ").strip().lower()
        is_agent_mode = mode == 'a'
        
        assistant = Assistant(agent_mode=is_agent_mode)
        if is_agent_mode:
            print("\n=== 已进入 Agent 模式 ===")
            print("AI 将自动执行命令来完成你的目标")
            print("你只需要描述你想完成的任务即可")
            print("示例：安装并配置 Nginx 服务器")
            assistant.terminal.agent_mode = is_agent_mode
        else:
            print("\n=== 已进入问答模式 ===")
            print("AI 将回答你的问题并提供建议")
            print("示例：如何安装 Nginx？")
        
        assistant.run()
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()