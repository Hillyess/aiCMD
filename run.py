from yunyan.core import Assistant
import sys

def main():
    try:
        assistant = Assistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
    except Exception as e:
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 