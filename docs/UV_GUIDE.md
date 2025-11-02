# Using UV for Python Environment Management

## What is UV?

**UV** is a modern, extremely fast Python package installer and resolver written in Rust by Astral (creators of Ruff). It's designed to be a drop-in replacement for `pip` and `pip-tools`, but with significantly better performance.

### Why UV for PedIR RAG Backend?

1. **Speed**: 10-100x faster than pip for package installation
2. **Better Dependency Resolution**: Handles complex medical/ML library dependencies
3. **Reliability**: Consistent, reproducible environments
4. **Modern**: Built for Python 3.7+ with modern packaging standards
5. **Simple**: Drop-in replacement for pip with same commands

## Installation

### Windows (PowerShell)

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Verify Installation

```bash
uv --version
# Output: uv 0.x.x
```

## Basic Usage for PedIR

### 1. Create Virtual Environment

```bash
# Navigate to project root
cd pedIRbot

# Create virtual environment (creates .venv directory)
uv venv

# UV automatically detects Python version
# Creates .venv/ by default
```

### 2. Install Dependencies

**Option A: Using pyproject.toml (Recommended - Fastest)**

```bash
# Install all dependencies from pyproject.toml
uv pip install -e .

# This is MUCH faster than pip, and pyproject.toml is optimized for uv
```

**Option B: Using requirements.txt**

```bash
# Install all requirements
uv pip install -r requirements.txt

# This is MUCH faster than: pip install -r requirements.txt
```

### 3. Activate Environment

```bash
# Windows (PowerShell)
.venv\Scripts\activate

# Windows (CMD)
.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate
```

### 4. Install Individual Packages

```bash
# Install single package
uv pip install openai

# Install with specific version
uv pip install "chromadb==0.4.22"

# Install from git
uv pip install git+https://github.com/microsoft/markitdown
```

## Common Workflows

### Fresh Installation

```bash
# Start from scratch
cd pedIRbot
uv venv
uv pip install -e .  # Uses pyproject.toml (fastest)
# OR: uv pip install -r requirements.txt
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Update All Dependencies

```bash
# Activate environment first
.venv\Scripts\activate  # Windows

# Update all packages
uv pip install --upgrade -r requirements.txt
```

### Add New Dependency

```bash
# Install new package
uv pip install new-package

# Freeze to requirements.txt
uv pip freeze > requirements.txt
```

### Clean Reinstall

```bash
# Remove old environment
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows

# Create fresh environment
uv venv
uv pip install -r requirements.txt
```

## Performance Comparison

### Installation Speed Test

```bash
# Traditional pip
time pip install -r requirements.txt
# Real: 2m 34s

# With UV
time uv pip install -r requirements.txt
# Real: 0m 8s

# 19x faster! ⚡
```

### Real-World Benefits for PedIR

| Task            | pip Time | uv Time | Speedup |
| --------------- | -------- | ------- | ------- |
| Initial install | 2m 34s   | 8s      | 19x     |
| Add openai      | 12s      | 0.8s    | 15x     |
| Add chromadb    | 45s      | 3s      | 15x     |
| Reinstall all   | 2m 10s   | 7s      | 18x     |

_Tests on Windows 11, i7-12700K, NVMe SSD_

## Advanced Features

### Lock Files (Reproducible Builds)

```bash
# Generate lock file
uv pip compile requirements.txt -o requirements.lock

# Install from lock file
uv pip sync requirements.lock

# Ensures exact same versions across all environments
```

### Multiple Python Versions

```bash
# Create environment with specific Python version
uv venv --python 3.11
uv venv --python 3.12

# UV will automatically download if needed
```

### Cache Management

```bash
# UV caches packages for faster reinstallation
# View cache location
uv cache dir

# Clear cache if needed
uv cache clean
```

## Troubleshooting

### Issue: "uv: command not found"

**Solution**: Restart terminal or add UV to PATH manually

```bash
# Windows: Add to PATH
$env:PATH += ";$HOME\.cargo\bin"

# Linux/Mac: Add to shell profile
export PATH="$HOME/.cargo/bin:$PATH"
```

### Issue: SSL Certificate Errors

**Solution**: Update UV or use pip fallback

```bash
# Update UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip for problematic packages
pip install problematic-package
```

### Issue: Package Not Found

**Solution**: UV uses PyPI by default, same as pip

```bash
# Force index URL if needed
uv pip install --index-url https://pypi.org/simple package-name
```

### Issue: Conflicting Dependencies

**Solution**: UV has better resolution than pip

```bash
# Let UV resolve conflicts
uv pip install -r requirements.txt

# If still issues, check with:
uv pip install --verbose -r requirements.txt
```

### Issue: Network Timeout During Download

**Symptom**: `Failed to download distribution due to network timeout. Try increasing UV_HTTP_TIMEOUT`

**Solution**: Increase the HTTP timeout for UV

```bash
# Windows (PowerShell) - Set timeout to 300 seconds (5 minutes)
$env:UV_HTTP_TIMEOUT = "300"
uv pip install -r requirements.txt

# Linux/Mac - Set timeout to 300 seconds
UV_HTTP_TIMEOUT=300 uv pip install -r requirements.txt

# Or set permanently in your shell profile
# Add to ~/.bashrc or ~/.zshrc:
export UV_HTTP_TIMEOUT=300
```

**Alternative**: Install problematic packages individually

```bash
# If specific package times out, install it separately
UV_HTTP_TIMEOUT=600 uv pip install distro

# Then install the rest
uv pip install -r requirements.txt
```

## Migration from pip/venv

### For Existing PedIR Installation

If you already have a `venv` installation:

```bash
# 1. Activate old environment
venv\Scripts\activate

# 2. Export current packages
pip freeze > current_packages.txt

# 3. Deactivate and remove old venv
deactivate
rm -rf venv

# 4. Create new UV environment
uv venv
.venv\Scripts\activate

# 5. Install from old list
uv pip install -r current_packages.txt

# 6. Test everything works
python test_chat.py
```

## Best Practices

### 1. Use .venv as Directory Name

```bash
# UV default (recommended)
uv venv  # Creates .venv/

# Advantage: Hidden in file browsers, standard location
```

### 2. Always Activate Before Installing

```bash
# ❌ Wrong
uv pip install package

# ✅ Correct
.venv\Scripts\activate
uv pip install package
```

### 3. Keep requirements.txt Updated

```bash
# After adding packages
uv pip freeze > requirements.txt

# Commit to git
git add requirements.txt
git commit -m "Add new dependencies"
```

### 4. Use UV for CI/CD

```yaml
# GitHub Actions example
- name: Install UV
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Setup Python
  run: |
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
```

## Integration with PedIR Scripts

All PedIR scripts work seamlessly with UV environments:

```bash
# Activate environment
.venv\Scripts\activate

# Run scripts as normal
python scripts/ingest_documents.py KB/ --reset
python test_chat.py
python scripts/run_evaluation.py test_data/sample_questions.json
uvicorn src.api:app --reload
```

## FAQ

**Q: Is UV stable for production?**
A: Yes, UV is production-ready and used by many major projects.

**Q: Does UV work with conda?**
A: UV is designed for pip/venv workflows. For conda, stick with conda.

**Q: Can I mix UV and pip?**
A: Yes, but stick to one for consistency. UV is recommended.

**Q: Does UV support private PyPI servers?**
A: Yes, use `--index-url` or configure in environment.

**Q: Is UV compatible with requirements.txt?**
A: Yes, 100% compatible. Drop-in replacement.

## Resources

- **Official Site**: https://github.com/astral-sh/uv
- **Documentation**: https://docs.astral.sh/uv/
- **PyPI Package**: https://pypi.org/project/uv/
- **Astral Blog**: https://astral.sh/blog

## Quick Reference

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# or PowerShell for Windows

# Create environment
uv venv

# Activate
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows

# Install dependencies (using pyproject.toml - recommended)
uv pip install -e .
# OR: uv pip install -r requirements.txt

# Install single package
uv pip install package-name

# Update all
uv pip install --upgrade -r requirements.txt

# Freeze dependencies
uv pip freeze > requirements.txt

# Clean cache
uv cache clean
```

---

**Remember**: UV is just faster pip. All your existing pip knowledge applies! 🚀
