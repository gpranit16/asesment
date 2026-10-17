import os
import sys
from pathlib import Path

# Add project root to sys.path so 'backend' package imports work cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Enterprise Multi-Agent API server on http://localhost:{port}")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True, app_dir=str(ROOT_DIR))
