#!/bin/bash

# --- Configuration ---
VENV_NAME="venv"
PYTHON_BIN="python3" # Use python3 for most Linux/macOS systems. On Windows, it might be 'python'.
                     # The script will try both.
CONFIG_FILE="config.yaml"
ENV_EXAMPLE="env.example"
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
check_command "pip"

# Determine Python command based on OS
if [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
    # macOS / Linux
    PYTHON_BIN="python3"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Git Bash / Cygwin on Windows
    PYTHON_BIN="python"
fi
check_command "$PYTHON_BIN"
echo_color green "Prerequisites checked: Git, Pip, and Python are available."

# --- Virtual Environment Setup ---
echo_color blue "\n--- Setting up virtual environment ---"

if [ -d "$VENV_NAME" ]; then
    echo_color yellow "Virtual environment '$VENV_NAME' already exists. Re-creating..."
    rm -rf "$VENV_NAME"
fi

echo_color blue "Creating virtual environment '$VENV_NAME'..."
"$PYTHON_BIN" -m venv "$VENV_NAME"
if [ $? -ne 0 ]; then
    echo_color red "Failed to create virtual environment."
    exit 1
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

# Set path for pip and python within the venv for this script's execution
VENV_PIP="$VENV_NAME/bin/pip"
VENV_PYTHON="$VENV_NAME/bin/python"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    VENV_PIP="$VENV_NAME/Scripts/pip"
    VENV_PYTHON="$VENV_NAME/Scripts/python"
fi


# --- Install Dependencies ---
echo_color blue "\n--- Installing dependencies ---"

echo_color blue "Installing runtime dependencies from requirements.txt..."
"$VENV_PIP" install -r requirements.txt
if [ $? -ne 0 ]; then
    echo_color red "Failed to install runtime dependencies."
    exit 1
fi
echo_color green "Runtime dependencies installed."

echo_color blue "Installing development dependencies from requirements-dev.txt..."
"$VENV_PIP" install -r requirements-dev.txt
if [ $? -ne 0 ]; then
    echo_color red "Failed to install development dependencies."
    exit 1
fi
echo_color green "Development dependencies installed."

echo_color blue "Installing project in editable mode..."
"$VENV_PIP" install -e .
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

# Check if config.yaml exists
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
echo_color yellow "$VENV_PYTHON main.py" # Explicitly use venv's python
echo_color blue "Or, after activating, simply:"
echo_color yellow "python main.py"
echo_color blue "Remember to fill in your API keys in '$DOT_ENV'."
