# aiCMD - AI 驱动的命令行助手

aiCMD 是一个智能的命令行界面，集成了 AI 功能，帮助用户更高效地完成运维工作。

## 特性

- **智能命令行界面**
  - 智能命令及路径补全
  - 多级目录补全
  - 命令历史记录跟踪
  - 命令输出捕获
  - 友好的提示显示

- **AI 助手功能**
  - 支持中文自然语言查询
  - 自动捕获命令执行上下文
  - 会话历史维护
  - 智能理解运维场景

- **交互体验**
  - 支持 Tab 键补全
  - 箭头键导航
  - Ctrl+C/D 快捷键
  - 空格/右箭头快速补全
  - 彩色输出提示

## 安装

```bash
# 通过 pip 安装
pip install aicmd

# 或者从源代码安装
git clone https://github.com/your-username/aicmd.git
cd aicmd
pip install -e .
```

## 依赖

- Python >= 3.7
- prompt_toolkit >= 3.0.0
- openai >= 1.0.0
- requests >= 2.25.1
- colorama >= 0.4.4

## 使用方法

1. 启动 aiCMD:
   ```bash
   ai
   ```

2. 使用 AI 助手:
   ```bash
   # 以 / 开头提问
   /how to check system status

   # 或者直接输入中文
   查看当前目录下的大文件
   ```

3. 执行命令:
   ```bash
   # 直接输入普通命令
   ls -la
   cd /path/to/dir
   ```

4. 使用补全功能:
   - 按 Tab 键显示补全选项
   - 使用箭头键选择
   - 按空格或右箭头确认选择
   - 对于目录，自动继续补全子目录

## 配置

aiCMD 会在您的主目录下创建以下文件：
- `~/.aicmd_history`：命令历史记录
- `~/.aicmd/config.yaml`：配置文件（如需要）

## 开发

1. 克隆仓库:
   ```bash
   git clone https://github.com/your-username/aicmd.git
   ```

2. 安装开发依赖:
   ```bash
   pip install -e ".[dev]"
   ```

3. 运行测试:
   ```bash
   pytest
   ```

## 贡献

欢迎提交 Pull Request 和 Issue！

## 许可

MIT 许可

## 作者

[Your Name] - [your-email@example.com]

## 鸣谢

- OpenAI - 提供 AI 能力
- prompt_toolkit - 提供优秀的命令行界面

## 项目描述
本项目旨在提供一套基于 Git 操作的命令行工具，帮助用户方便快捷地进行代码提交和版本管理。当前功能已经支持基本的 Git 操作，如状态查看、文件添加、提交、更改记录修改、远程仓库管理等。

## 当前功能
- **Git 状态查看**：通过 `git status` 命令检查当前工作区状态。
- **文件添加和提交**：使用 `git add` 与 `git commit` 实现代码提交，并支持修改最近一次提交（`git commit --amend`）。
- **远程仓库管理**：包括远程仓库的添加、删除、更新，以及通过 `git push -u` 设置上游分支。

## 使用说明
1. 查看当前 Git 状态：
   ```bash
   git status
   ```
2. 添加文件：
   ```bash
   git add .
   ```
3. 提交更新：
   ```bash
   git commit -m "你的提交信息"
   ```
4. 修改最近一次提交：
   ```bash
   git commit --amend -m "新的提交信息"
   ```
5. 设置远程仓库（如有需要）：
   ```bash
   git remote add origin 远程仓库URL
   ```
6. 推送到远程仓库：
   ```bash
   # 第一次推送时设置上游分支
   git push -u origin main
   # 后续推送
   git push
   ```

## 常见问题排查
- **远程仓库重复添加错误**：当遇到 `error: remote origin already exists` 时，请先移除现有的远程仓库：
  ```bash
  git remote remove origin
  git remote add origin 远程仓库URL
  ```
- **上游分支未设置**：出现 `fatal: The current branch main has no upstream branch` 错误时，请使用：
  ```bash
  git push -u origin main
  ```
- **其他常见问题**：请参考 Git 官方文档或相关社区讨论。

## 下一步迭代计划
- **联网搜索功能**：计划实现联网搜索功能，支持在线检索相关的资源、文档和代码示例，从而提升开发效率。
- **CMDB 数据库读取功能**：计划集成 CMDB（配置管理数据库）读取接口，实现对系统配置信息的自动查询和管理。

## 开发与贡献
欢迎提交您的建议和代码贡献！请在贡献前阅读贡献指南，然后通过 issue 或 pull request 的方式参与项目开发。 