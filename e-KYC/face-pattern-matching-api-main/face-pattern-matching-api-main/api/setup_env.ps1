# setup_env.ps1

# Check if uv is installed, if not install it
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    pip install uv
}

Write-Host "Creating virtual environment..."
uv venv

Write-Host "Activating venv and installing requirements..."
# Use uv pip install which is extremely fast and automatically uses the venv if present
uv pip install -r requirements.txt

Write-Host "================================================="
Write-Host "Setup complete!"
Write-Host "To activate the virtual environment, run:"
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host "Then, start the FastAPI server with:"
Write-Host "    uvicorn main:app --reload"
Write-Host "================================================="
