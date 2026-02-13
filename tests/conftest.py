import os
import sys
from pathlib import Path


os.environ.setdefault("KIVY_NO_ARGS", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
