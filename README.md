# aiCMD - AI-Powered Command-Line Assistant

aiCMD is an intelligent command-line interface that integrates AI capabilities to help users better complete their operations and maintenance work.

## Features

- Intelligent Command-Line Interface
  - Smart command and path completion
  - Multi-level directory completion
  - Command history tracking
  - Command output capture
  - User-friendly prompt display

- AI Assistant Features
  - Support for Chinese natural language queries
  - Automatic command execution context capture
  - Conversation history maintenance
  - Intelligent understanding of operations scenarios

- Interactive Experience
  - Tab completion support
  - Arrow key navigation
  - Ctrl+C/D shortcuts
  - Space/Right arrow quick completion
  - Colored output prompts

## Installation

```bash
# Install via pip
pip install aicmd

# Or install from source
git clone https://github.com/your-username/aicmd.git
cd aicmd
pip install -e .
```

## Dependencies

- Python >= 3.7
- prompt_toolkit >= 3.0.0
- openai >= 1.0.0
- requests >= 2.25.1
- colorama >= 0.4.4

## Usage

1. Start aiCMD:
```bash
ai
```

2. Use AI Assistant:
```bash
# Ask questions starting with /
/how to check system status

# Or directly input Chinese
查看当前目录下的大文件
```

3. Execute Commands:
```bash
# Direct input of regular commands
ls -la
cd /path/to/dir
```

4. Use Completion:
- Press Tab to show completion options
- Use arrow keys to select
- Press space or right arrow to confirm selection
- For directories, automatically continue completing subdirectories

## Configuration

aiCMD creates the following files in your home directory:
- `~/.aicmd_history`: Command history
- `~/.aicmd/config.yaml`: Configuration file (if needed)

## Development

1. Clone repository:
```bash
git clone https://github.com/your-username/aicmd.git
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## Contributing

Pull Requests and Issues are welcome!

## License

MIT License

## Author

[Your Name] - [your-email@example.com]

## Acknowledgments

- OpenAI - Providing AI capabilities
- prompt_toolkit - Providing excellent command-line interface 