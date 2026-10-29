
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

def main():
    event = json.load(sys.stdin)
    prompt = event.get("prompt", "")
    if not prompt.strip():
        return

    project = Path(
        os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", "."))
    ).resolve()

    log_dir = project / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "prompts.md"

    timestamp = datetime.now(timezone.utc).isoformat()

    with log_file.open("a", encoding="utf-8") as f:
        f.write(
            f"\n## Prompt\n\n"
            "````text\n"
            f"{prompt}\n"
            "````\n\n---\n"
        )

if __name__ == "__main__":
    main()
