# Development Tasks Configuration

This document contains the VSCode tasks configuration for the ChoreAssistant project. The content below should be saved as `.vscode/tasks.json` in the project root.

## Tasks Configuration (tasks.json)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Install Development Dependencies",
      "type": "shell",
      "command": "pip",
      "args": [
        "install",
        "-r",
        "requirements-dev.txt"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Install Python development dependencies including testing and linting tools"
    },
    {
      "label": "Run Unit Tests",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--cov=custom_components/chore_assistant",
        "--cov-report=html",
        "--cov-report=term"
      ],
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [
        {
          "owner": "python",
          "fileLocation": [
            "relative",
            "${workspaceFolder}"
          ],
          "pattern": {
            "regexp": "^(.*):(\\d+):(\\d+):\\s+(warning|error):\\s+(.*)$",
            "file": 1,
            "line": 2,
            "column": 3,
            "severity": 4,
            "message": 5
          }
        }
      ],
      "detail": "Run unit tests with coverage reporting"
    },
    {
      "label": "Run Integration Tests",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
      ],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Run integration tests against Home Assistant"
    },
    {
      "label": "Run All Tests",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--cov=custom_components/chore_assistant",
        "--cov-report=html",
        "--cov-report=term",
        "--tb=short"
      ],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Run all tests (unit and integration) with coverage"
    },
    {
      "label": "Lint Code (Black)",
      "type": "shell",
      "command": "black",
      "args": [
        "custom_components/chore_assistant/",
        "tests/",
        "--check",
        "--diff"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [
        {
          "owner": "black",
          "fileLocation": [
            "relative",
            "${workspaceFolder}"
          ],
          "pattern": {
            "regexp": "^would reformat (.*)$",
            "file": 1,
            "severity": "warning",
            "message": "File would be reformatted by Black"
          }
        }
      ],
      "detail": "Check code formatting with Black"
    },
    {
      "label": "Format Code (Black)",
      "type": "shell",
      "command": "black",
      "args": [
        "custom_components/chore_assistant/",
        "tests/"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Format code with Black"
    },
    {
      "label": "Lint Code (Flake8)",
      "type": "shell",
      "command": "flake8",
      "args": [
        "custom_components/chore_assistant/",
        "tests/",
        "--config=.flake8"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [
        {
          "owner": "flake8",
          "fileLocation": [
            "relative",
            "${workspaceFolder}"
          ],
          "pattern": {
            "regexp": "^(.*):(\\d+):(\\d+):\\s+([A-Z]\\d+)\\s+(.*)$",
            "file": 1,
            "line": 2,
            "column": 3,
            "code": 4,
            "message": 5,
            "severity": "warning"
          }
        }
      ],
      "detail": "Lint code with Flake8"
    },
    {
      "label": "Type Check (MyPy)",
      "type": "shell",
      "command": "mypy",
      "args": [
        "custom_components/chore_assistant/",
        "--config-file=mypy.ini"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [
        {
          "owner": "mypy",
          "fileLocation": [
            "relative",
            "${workspaceFolder}"
          ],
          "pattern": {
            "regexp": "^(.*):(\\d+):(\\d+):\\s+(error|warning|note):\\s+(.*)$",
            "file": 1,
            "line": 2,
            "column": 3,
            "severity": 4,
            "message": 5
          }
        }
      ],
      "detail": "Run static type checking with MyPy"
    },
    {
      "label": "Security Check (Bandit)",
      "type": "shell",
      "command": "bandit",
      "args": [
        "-r",
        "custom_components/chore_assistant/",
        "-f",
        "json",
        "-o",
        "bandit-report.json"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Run security analysis with Bandit"
    },
    {
      "label": "Generate Documentation",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "pydoc",
        "-w",
        "custom_components.chore_assistant"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Generate API documentation with pydoc"
    },
    {
      "label": "Validate Home Assistant Config",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "homeassistant",
        "--script",
        "check_config",
        "--config",
        "tests/fixtures/config"
      ],
      "group": "test",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Validate Home Assistant configuration with test fixtures"
    },
    {
      "label": "Build Distribution Package",
      "type": "shell",
      "command": "python",
      "args": [
        "setup.py",
        "sdist",
        "bdist_wheel"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Build distribution packages for release"
    },
    {
      "label": "Clean Build Artifacts",
      "type": "shell",
      "command": "python",
      "args": [
        "setup.py",
        "clean",
        "--all"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Clean build artifacts and temporary files"
    },
    {
      "label": "Start Home Assistant Dev Server",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "homeassistant",
        "--config",
        "tests/fixtures/config",
        "--debug"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Start Home Assistant development server with test configuration",
      "isBackground": true,
      "runOptions": {
        "instanceLimit": 1
      }
    },
    {
      "label": "Run Pre-commit Hooks",
      "type": "shell",
      "command": "pre-commit",
      "args": [
        "run",
        "--all-files"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Run all pre-commit hooks on all files"
    },
    {
      "label": "Update Dependencies",
      "type": "shell",
      "command": "pip-compile",
      "args": [
        "requirements.in",
        "--upgrade"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Update and compile Python dependencies"
    },
    {
      "label": "Full Quality Check",
      "dependsOrder": "sequence",
      "dependsOn": [
        "Lint Code (Black)",
        "Lint Code (Flake8)",
        "Type Check (MyPy)",
        "Security Check (Bandit)",
        "Run All Tests"
      ],
      "group": {
        "kind": "build",
        "isDefault": true
      },
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Run complete quality assurance pipeline"
    },
    {
      "label": "Prepare Release",
      "dependsOrder": "sequence",
      "dependsOn": [
        "Full Quality Check",
        "Generate Documentation",
        "Build Distribution Package"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Prepare project for release (QA + docs + build)"
    },
    {
      "label": "Quick Development Check",
      "dependsOrder": "sequence",
      "dependsOn": [
        "Format Code (Black)",
        "Lint Code (Flake8)",
        "Run Unit Tests"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": [],
      "detail": "Quick development workflow (format + lint + unit tests)"
    }
  ]
}
```

## Task Categories

### Build Tasks
- **Install Development Dependencies**: Set up the development environment
- **Format Code (Black)**: Automatically format Python code
- **Lint Code (Black/Flake8)**: Check code style and quality
- **Type Check (MyPy)**: Static type analysis
- **Security Check (Bandit)**: Security vulnerability scanning
- **Generate Documentation**: Create API documentation
- **Build Distribution Package**: Create release packages
- **Clean Build Artifacts**: Remove temporary files

### Test Tasks
- **Run Unit Tests**: Execute unit tests with coverage (default test task)
- **Run Integration Tests**: Execute integration tests
- **Run All Tests**: Complete test suite execution
- **Validate Home Assistant Config**: Validate configuration files

### Development Tasks
- **Start Home Assistant Dev Server**: Launch development server
- **Update Dependencies**: Update Python package dependencies
- **Run Pre-commit Hooks**: Execute git pre-commit hooks

### Composite Tasks
- **Full Quality Check**: Complete QA pipeline (default build task)
- **Prepare Release**: Full release preparation workflow
- **Quick Development Check**: Fast development iteration workflow

## Usage Instructions

1. **Copy to VSCode Configuration**:
   ```bash
   mkdir -p .vscode
   # Copy the JSON content above to .vscode/tasks.json
   ```

2. **Run Tasks**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Tasks: Run Task"
   - Select the desired task from the list

3. **Keyboard Shortcuts**:
   - `Ctrl+Shift+B`: Run default build task (Full Quality Check)
   - `Ctrl+Shift+T`: Run default test task (Run Unit Tests)

4. **Task Dependencies**:
   - Some tasks depend on others and will run them automatically
   - Composite tasks run multiple related tasks in sequence
   - Failed dependencies will stop the task chain

## Required Development Dependencies

Create a `requirements-dev.txt` file with:

```txt
# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-homeassistant-custom-component>=0.13.0
pytest-asyncio>=0.21.0

# Code Quality
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
bandit>=1.7.0
pre-commit>=3.0.0

# Documentation
pydoc-markdown>=4.0.0
sphinx>=6.0.0
sphinx-rtd-theme>=1.2.0

# Development Tools
pip-tools>=6.0.0
homeassistant>=2023.1.0
voluptuous>=0.13.0
```

## Configuration Files

### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info
```

### mypy.ini
```ini
[mypy]
python_version = 3.11
show_error_codes = True
follow_imports = silent
ignore_missing_imports = True
strict_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_unreachable = True
warn_unused_configs = True

[mypy-homeassistant.*]
ignore_missing_imports = True

[mypy-voluptuous.*]
ignore_missing_imports = True
```

### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

## Integration with CI/CD

These tasks can be integrated with GitHub Actions or other CI/CD systems:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: black --check custom_components/ tests/
      - run: flake8 custom_components/ tests/
      - run: mypy custom_components/
      - run: bandit -r custom_components/
      - run: pytest tests/ --cov=custom_components/chore_assistant
```

This tasks configuration provides a comprehensive development workflow for the ChoreAssistant project, supporting code quality, testing, documentation, and release preparation.