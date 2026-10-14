from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repodoctor.llm.factory import make_llm


if __name__ == "__main__":
    model = os.getenv("REPO_DOCTOR_GEMINI_MODEL", "gemini-2.5-flash-lite")
    llm = make_llm("gemini", model)
    out = llm.generate(
        'Return only JSON: {"status": "ok", "message": "Gemini is connected"}'
    )
    print(out)
