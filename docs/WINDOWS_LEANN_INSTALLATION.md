# LEANN Installation on Windows

## Problem

LEANN's `leann-backend-hnsw` package does not have pre-built wheels for Windows, causing installation failures:

```
× No solution found when resolving dependencies:
  ╰─▶ Because all versions of leann-backend-hnsw have no wheels with a matching
      Python implementation tag, we can conclude that leann-backend-hnsw cannot be used.
```

## Solutions

### Option 1: Use WSL (Windows Subsystem for Linux) - **Recommended**

WSL allows you to run a Linux environment on Windows, where LEANN installs normally.

#### Steps:

1. **Install WSL**:
   ```powershell
   wsl --install
   ```
   Or follow: https://docs.microsoft.com/en-us/windows/wsl/install

2. **Open WSL terminal** and navigate to your project:
   ```bash
   cd /mnt/d/Development\ area/pedIRbot
   ```

3. **Set up Python environment in WSL**:
   ```bash
   # Install Python if needed
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install leann
   ```

4. **Run your application from WSL**:
   ```bash
   python scripts/ingest_documents_leann.py KB/md --reset
   ```

**Pros**:
- Easiest solution
- Full Linux compatibility
- No code changes needed

**Cons**:
- Requires WSL installation
- Need to work in WSL terminal

---

### Option 2: Build from Source (Advanced)

Build `leann-backend-hnsw` from source on Windows.

#### Prerequisites:

1. **Visual Studio Build Tools**:
   - Download: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload

2. **CMake** (if not included):
   - Download: https://cmake.org/download/
   - Add to PATH

#### Steps:

1. **Clone LEANN repository**:
   ```powershell
   git clone https://github.com/yichuan-w/LEANN.git
   cd LEANN
   ```

2. **Build backend**:
   ```powershell
   cd packages/leann-backend-hnsw
   python setup.py build_ext --inplace
   python setup.py install
   ```

3. **Install main package**:
   ```powershell
   cd ../..
   pip install -e .
   ```

**Pros**:
- Works natively on Windows
- No WSL needed

**Cons**:
- Complex setup
- Requires C++ compiler
- May have compatibility issues
- Time-consuming

---

### Option 3: Use Docker/Linux Container

Run your application in a Linux container.

#### Steps:

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install leann
   COPY . .
   CMD ["python", "scripts/ingest_documents_leann.py", "KB/md"]
   ```

2. **Build and run**:
   ```powershell
   docker build -t pedirbot-leann .
   docker run -v ${PWD}/KB:/app/KB pedirbot-leann
   ```

**Pros**:
- Isolated environment
- Works on any platform

**Cons**:
- Requires Docker
- More complex deployment

---

### Option 4: Continue Using ChromaDB

LEANN is not required - ChromaDB works perfectly fine on Windows.

The LEANN implementation is ready for when Windows support is available, but you can continue using ChromaDB:

```python
from src.vector_store import VectorStore  # ChromaDB - works on Windows
# from src.vector_store_leann import LEANNVectorStore  # LEANN - Windows support pending
```

**Pros**:
- Works immediately
- No setup needed
- Stable and tested

**Cons**:
- No storage savings (but storage is usually not a bottleneck)
- Missing LEANN's optimizations

---

## Recommendation

**For development**: Use **Option 1 (WSL)** - it's the easiest and most reliable.

**For production**:
- If deploying to Linux servers: Use LEANN
- If Windows-only: Continue with ChromaDB or use Docker

## Checking LEANN Windows Support

Monitor LEANN's GitHub for Windows wheel updates:
- https://github.com/yichuan-w/LEANN/issues
- https://pypi.org/project/leann-backend-hnsw/

When Windows wheels become available, installation will work normally:

```bash
uv pip install leann
```

## Current Status

As of now, LEANN does not have Windows wheels. The implementation code is ready and will work once Windows support is added. Until then, use one of the solutions above or continue with ChromaDB.



