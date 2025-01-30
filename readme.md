# Code Analysis Chat Tool

This tool provides an interactive chat interface for analyzing code repositories using GPT-4 and various code analysis tools. It combines the power of Autogen and Composio to provide detailed code analysis capabilities.

## Prerequisites

- Python 3.12
- Valid API keys for:
  - Composio (`COMPOSIO_API_KEY`)
  - OpenAI (`OPENAI_API_KEY`)
  - GitHub (`GITHUB_ACCESS_TOKEN`)

## Installation

1. Clone the repository
2. Ensure you have Python 3.12 installed:
```bash
python --version  # Should output Python 3.12.x
```

3. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

4. Install the required dependencies:
```bash
pip install -r requirements.txt
```

5. Set up your environment variables:
```bash
export COMPOSIO_API_KEY="your_composio_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export GITHUB_ACCESS_TOKEN="your_github_token"
```

## Requirements

Create a `requirements.txt` file with the following dependencies:
```
composio==1.0.0
composio-autogen==1.0.0
autogen==1.0.0
python-dotenv==1.0.0
```

## Usage

1. Run the script:
```bash
python main.py
```

2. When prompted, enter the directory path of the repository you want to analyze.

3. The tool will initialize and create a code map of the repository.

4. You can then enter questions about the codebase. The tool provides access to several analysis capabilities:
   - Class information retrieval
   - Method body analysis
   - Method signature lookup
   - File content viewing
   - Word search across the repository
   - File finding

5. Type 'exit' to quit the program.

## Available Tools

The tool provides the following analysis capabilities:
- `CODE_ANALYSIS_TOOL_GET_CLASS_INFO`: Get information about classes
- `CODE_ANALYSIS_TOOL_GET_METHOD_BODY`: Retrieve method implementations
- `CODE_ANALYSIS_TOOL_GET_METHOD_SIGNATURE`: Get method signatures
- `CODE_ANALYSIS_TOOL_GET_RELEVANT_CODE`: Find relevant code snippets
- `FILETOOL_OPEN_FILE`: View file contents
- `FILETOOL_SCROLL`: Navigate through files
- `FILETOOL_SEARCH_WORD`: Search for specific terms
- `FILETOOL_FIND_FILE`: Locate files in the repository

## Special Features

- Batch input: Type 'file' instead of a question to read input from 'input.txt'
- Caching: Results are cached to improve performance
- Round-robin speaker selection for chat management
- Maximum of 20 rounds per conversation

## Environment Variables

Required environment variables:
```
COMPOSIO_API_KEY=your_composio_api_key
OPENAI_API_KEY=your_openai_api_key
GITHUB_ACCESS_TOKEN=your_github_token
```

## Notes

- The tool is designed to analyze API service repositories
- It can identify main entry points and list available APIs
- Each analysis provides structured information about endpoints, HTTP methods, parameters, and response formats

## Limitations

- File viewing is limited to 100 lines at a time
- The chat has a maximum of 20 rounds per conversation
- Requires valid API keys for all services
- Docker execution is disabled by default
- Compatible with Python 3.12

## Troubleshooting

If you encounter any issues:
1. Ensure you're using Python 3.12
2. Verify all environment variables are set correctly
3. Make sure you have the correct permissions for the repository you're analyzing
4. Check that all API keys are valid and have the necessary permissions
