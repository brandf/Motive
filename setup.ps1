<#
.SYNOPSIS
    Sets up the Python development environment for the AI Game Master project on Windows (PowerShell).
.DESCRIPTION
    This script performs the following actions:
    1. Checks for Python and Pip installation.
    2. Creates a Python virtual environment named 'venv'.
    3. Activates the virtual environment.
    4. Installs runtime dependencies from 'requirements.txt'.
    5. Installs development dependencies from 'requirements-dev.txt'.
    6. Creates a 'logs/' directory if it doesn't exist.
    7. Copies 'env.example' to '.env' if '.env' does not exist, and reminds the user to fill in API keys.
    8. Verifies the presence of 'config.yaml'.
.NOTES
    Author: T3 Chat (Modified by user request)
    Version: 1.0
    Date: September 7, 2025
    Requirements:
        - PowerShell 5.1 or later (Windows 10 / Windows Server 2016 and up).
        - Python (3.x recommended) installed and added to the System PATH.
#>

# --- Configuration ---
$VenvName = "venv"
$PythonExe = "py" # Use py launcher for Windows
$ConfigFileName = "config.yaml"
$EnvExampleName = "env.example.txt"
$DotEnvName = ".env"
$LogsDir = "logs"
$RequirementsFile = "requirements.txt"
$RequirementsDevFile = "requirements-dev.txt"

# --- Helper Functions ---
function Write-Color {
    param (
        [string]$Color,
        [string]$Message
    )
    switch ($Color) {
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        default { Write-Host $Message }
    }
}

function Check-Command {
    param (
        [string]$Command
    )
    if (-not (Get-Command -Name $Command -ErrorAction SilentlyContinue)) {
        Write-Color Red "Error: '$Command' is not installed or not in your PATH."
        Write-Color Red "Please install '$Command' to continue. Ensure Python is installed and added to PATH."
        exit 1
    }
}

# --- Pre-requisite Checks ---
Write-Color Blue "--- Checking system prerequisites ---"
Check-Command $PythonExe
# Check for pip through Python launcher
try {
    & $PythonExe -m pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Color Red "Error: pip is not available through '$PythonExe -m pip'."
        Write-Color Red "Please ensure pip is installed with your Python installation."
        exit 1
    }
} catch {
    Write-Color Red "Error: pip is not available through '$PythonExe -m pip'."
    Write-Color Red "Please ensure pip is installed with your Python installation."
    exit 1
}

# Ensure Python version is suitable
try {
    $pythonVersion = (& $PythonExe -c "import sys; print(sys.version_info.major)")
    if ($pythonVersion -ne 3) {
        Write-Color Red "Error: Python 3.x is required. Detected Python $pythonVersion."
        Write-Color Red "Please ensure 'python.exe' in your PATH points to a Python 3 installation."
        exit 1
    }
} catch {
    Write-Color Red "Error checking Python version. Ensure Python is correctly installed."
    exit 1
}

Write-Color Green "Prerequisites checked: Python and Pip are available."

# --- Virtual Environment Setup ---
Write-Color Blue "`n--- Setting up virtual environment ---"

if (Test-Path -Path $VenvName -PathType Container) {
    Write-Color Yellow "Virtual environment '$VenvName' already exists. Removing and re-creating..."
    Remove-Item -Path $VenvName -Recurse -Force
}

Write-Color Blue "Creating virtual environment '$VenvName'..."
& $PythonExe -m venv $VenvName
if ($LASTEXITCODE -ne 0) {
    Write-Color Red "Failed to create virtual environment."
    exit 1
}
Write-Color Green "Virtual environment created."

# Define paths to venv executables
$VenvPython = Join-Path (Join-Path $VenvName "Scripts") "python.exe"
$VenvPip = Join-Path (Join-Path $VenvName "Scripts") "pip.exe"
$VenvActivateScript = Join-Path (Join-Path $VenvName "Scripts") "Activate.ps1"

# --- Install Dependencies ---
Write-Color Blue "`n--- Installing dependencies ---"

# Need to run pip directly from the venv path before activating fully,
# as activation is for the current shell's PATH.

Write-Color Blue "Installing runtime dependencies from $RequirementsFile..."
& $VenvPip install -r $RequirementsFile
if ($LASTEXITCODE -ne 0) {
    Write-Color Red "Failed to install runtime dependencies."
    exit 1
}
Write-Color Green "Runtime dependencies installed."

Write-Color Blue "Installing development dependencies from $RequirementsDevFile..."
& $VenvPip install -r $RequirementsDevFile
if ($LASTEXITCODE -ne 0) {
    Write-Color Red "Failed to install development dependencies."
    exit 1
}
Write-Color Green "Development dependencies installed."

Write-Color Blue "Installing project in editable mode..."
& $VenvPip install -e .
if ($LASTEXITCODE -ne 0) {
    Write-Color Red "Failed to install project in editable mode."
    exit 1
}
Write-Color Green "Project installed in editable mode."

# --- Configuration and Logs Setup ---
Write-Color Blue "`n--- Setting up configuration and logs ---"

# Create logs directory if it doesn't exist
if (-not (Test-Path -Path $LogsDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-Color Green "Created '$LogsDir' directory."
} else {
    Write-Color Yellow "'$LogsDir' directory already exists."
}

# Copy env.example to .env if .env doesn't exist
if (-not (Test-Path -Path $DotEnvName -PathType Leaf)) {
    if (Test-Path -Path $EnvExampleName -PathType Leaf) {
        Copy-Item -Path $EnvExampleName -Destination $DotEnvName | Out-Null
        Write-Color Green "Copied '$EnvExampleName' to '$DotEnvName'."
        Write-Color Yellow "Please open '$DotEnvName' and fill in your API keys."
    } else {
        Write-Color Red "Warning: '$EnvExampleName' not found. Cannot create a template for '$DotEnvName'."
    }
} else {
    Write-Color Yellow "'$DotEnvName' already exists. Please ensure your API keys are set."
}

# Check if config.yaml exists
if (-not (Test-Path -Path $ConfigFileName -PathType Leaf)) {
    Write-Color Red "Error: '$ConfigFileName' not found. Please ensure it is in the project root."
    exit 1
}
Write-Color Green "Configuration files checked."


# --- Completion ---
Write-Color Blue "`n--- Setup Complete! ---"
Write-Color Green "Your Python project environment is ready."
Write-Color Blue "To activate your virtual environment, run:"
Write-Color Yellow ".\\$VenvName\\Scripts\\Activate.ps1"
Write-Color Blue "Then you can run your application with:"
Write-Color Yellow "$VenvPython main.py"
Write-Color Blue "Or, after activating, simply:"
Write-Color Yellow "python main.py"
Write-Color Blue "Remember to fill in your API keys in '$DotEnvName'."

