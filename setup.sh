#!/bin/bash

set -o pipefail

# --- Configuration ---
VENV_NAME="venv"
CONFIG_FILE="configs/game.yaml"
ENV_EXAMPLE="env.example.txt"
DOT_ENV=".env"
LOGS_DIR="logs"

# --- Helper Functions ---
echo_color() {
    COLOR=$1
    MESSAGE=$2
    case "$COLOR" in
        "green")    echo -e "\033[0;32m$MESSAGE\033[0m" ;; # Green
        "yellow")   echo -e "\033[0;33m$MESSAGE\033[0m" ;; # Yellow
        "red")      echo -e "\033[0;31m$MESSAGE\033[0m" ;; # Red
        "blue")     echo -e "\033[0;34m$MESSAGE\033[0m" ;; # Blue
        *)          echo "$MESSAGE" ;;
    esac
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo_color red "Error: '$1' is not installed or not in your PATH."
        echo_color red "Please install '$1' to continue. On macOS, use 'brew install $1'."
        echo_color red "On Windows, ensure Python is installed and added to PATH."
        exit 1
    fi
}

# --- Pre-requisite Checks ---
echo_color blue "--- Checking system prerequisites ---"
check_command "git"

PYTHON_BIN=""
for candidate in python3 python; do
    if command -v "$candidate" &> /dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo_color red "Error: Python 3 is required but was not found in PATH."
    echo_color red "Install Python 3 (e.g., 'sudo apt install python3 python3-pip python3-venv' on Ubuntu/WSL)."
    exit 1
fi

PY_MAJOR=$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.major)')
if [ "$PY_MAJOR" -ne 3 ]; then
    echo_color red "Error: Python 3 is required. Detected '$("$PYTHON_BIN" -V)'."
    exit 1
fi

if ! "$PYTHON_BIN" -m pip --version &> /dev/null; then
    echo_color red "Error: pip is not available for $PYTHON_BIN."
    echo_color red "Install pip with 'sudo apt install python3-pip' (Ubuntu/WSL) or the equivalent for your distro."
    exit 1
fi

echo_color green "Prerequisites checked: Git, Python 3, and pip are available."

# --- Virtual Environment Setup ---
echo_color blue "\n--- Setting up virtual environment ---"

if [ -d "$VENV_NAME" ]; then
    echo_color yellow "Virtual environment '$VENV_NAME' already exists. Re-creating..."
    rm -rf "$VENV_NAME"
fi

echo_color blue "Creating virtual environment '$VENV_NAME'..."
if ! "$PYTHON_BIN" -m venv "$VENV_NAME"; then
    echo_color yellow "Virtual environment creation reported a failure. Attempting manual pip bootstrap..."
    VENV_BOOTSTRAP_PY=""
    for candidate in "$VENV_NAME/bin/python" "$VENV_NAME/Scripts/python" "$VENV_NAME/Scripts/python.exe"; do
        if [ -x "$candidate" ]; then
            VENV_BOOTSTRAP_PY="$candidate"
            break
        fi
    done

    if [ -n "$VENV_BOOTSTRAP_PY" ]; then
        if "$VENV_BOOTSTRAP_PY" -m ensurepip --upgrade --default-pip; then
            echo_color yellow "Manual pip bootstrap succeeded. Continuing with setup..."
        else
            echo_color red "Failed to bootstrap pip after virtual environment creation error."
            if command -v apt-get &> /dev/null; then
                echo_color red "Tip: On Ubuntu/WSL install the venv module: sudo apt update && sudo apt install python3-venv"
            fi
            exit 1
        fi
    else
        echo_color red "Failed to locate python executable inside '$VENV_NAME'."
        if command -v apt-get &> /dev/null; then
            echo_color red "Tip: On Ubuntu/WSL install the venv module: sudo apt update && sudo apt install python3-venv"
        fi
        exit 1
    fi
fi
echo_color green "Virtual environment created."

# Activate virtual environment
# For subshells and direct execution, sourcing is necessary for the current shell
# However, for a script that then exits, it's better to explicitly use venv's python/pip
# For activation, we'll suggest manual activation.
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash/Cygwin)
    VENV_ACTIVATE_SCRIPT="./$VENV_NAME/Scripts/activate"
else
    # macOS/Linux
    VENV_ACTIVATE_SCRIPT="./$VENV_NAME/bin/activate"
fi

# Set path for python within the venv for this script's execution
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    VENV_BIN_DIR="$VENV_NAME/Scripts"
else
    VENV_BIN_DIR="$VENV_NAME/bin"
fi

VENV_PYTHON="$VENV_BIN_DIR/python"

if [ ! -x "$VENV_PYTHON" ]; then
    echo_color red "Virtual environment python executable not found at '$VENV_PYTHON'."
    exit 1
fi


# --- Install Dependencies ---
echo_color blue "\n--- Installing dependencies ---"

echo_color blue "Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo_color red "Failed to upgrade pip inside the virtual environment."
    exit 1
fi
echo_color green "pip upgraded."

echo_color blue "Installing runtime dependencies from requirements.txt..."
"$VENV_PYTHON" -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo_color red "Failed to install runtime dependencies."
    exit 1
fi
echo_color green "Runtime dependencies installed."

echo_color blue "Installing development dependencies from requirements-dev.txt..."
if [ -f requirements-dev.txt ]; then
    "$VENV_PYTHON" -m pip install -r requirements-dev.txt
    if [ $? -ne 0 ]; then
        echo_color red "Failed to install development dependencies."
        exit 1
    fi
    echo_color green "Development dependencies installed."
else
    echo_color yellow "requirements-dev.txt not found; skipping development dependencies."
fi

echo_color blue "Installing project in editable mode..."
"$VENV_PYTHON" -m pip install -e .
if [ $? -ne 0 ]; then
    echo_color red "Failed to install project in editable mode."
    exit 1
fi
echo_color green "Project installed in editable mode."


# --- Configuration and Logs Setup ---
echo_color blue "\n--- Setting up configuration and logs ---"

# Create logs directory if it doesn't exist
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo_color green "Created '$LOGS_DIR' directory."
else
    echo_color yellow "'$LOGS_DIR' directory already exists."
fi

# Copy env.example to .env if .env doesn't exist
if [ ! -f "$DOT_ENV" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$DOT_ENV"
        echo_color green "Copied '$ENV_EXAMPLE' to '$DOT_ENV'."
        echo_color yellow "Please open '$DOT_ENV' and fill in your API keys."
    else
        echo_color red "Warning: '$ENV_EXAMPLE' not found. Cannot create a template for '$DOT_ENV'."
    fi
else
    echo_color yellow "'$DOT_ENV' already exists. Please ensure your API keys are set."
fi

# Check if configs/game.yaml exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo_color red "Error: '$CONFIG_FILE' not found. Please ensure it is in the project root."
    exit 1
fi
echo_color green "Configuration files checked."


# --- Completion ---
echo_color blue "\n--- Setup Complete! ---"
echo_color green "Your Python project environment is ready."
echo_color blue "To activate your virtual environment, run:"
echo_color yellow "source $VENV_ACTIVATE_SCRIPT"
echo_color blue "Then you can run your application with:"
echo_color yellow "motive                                    # Run with default config"
echo_color yellow "motive -c tests/configs/integration/game_test.yaml         # Run test configuration"
echo_color yellow "motive-analyze                           # Analyze configurations"
echo_color blue "Or, after activating, you can also use:"
echo_color yellow "python -m motive.main                    # Alternative way to run"
echo_color blue "Remember to fill in your API keys in '$DOT_ENV'."
