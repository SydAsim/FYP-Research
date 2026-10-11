"""Normal terminal entrypoint; does not import or require Codex."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from research.execution_linux_v1.runner import entrypoint  # noqa: E402

if __name__ == "__main__":
    entrypoint()
