"""Round-trip migrations only on a newly created isolated validation database."""

import json
import os
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql

from research.remedies.preserve import OUTPUT, ROOT
from research.remedies.runtime import DATABASE


def main() -> None:
    name = f"readiness_migrations_{uuid4().hex}"
    with psycopg.connect(DATABASE, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    env = {**os.environ, "DATABASE_ADMIN_URL": DATABASE.rsplit("/", 1)[0].replace(
        "postgresql://", "postgresql+psycopg://"
    ) + "/" + name}
    results = []
    for action, target in (("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")):
        command = [sys.executable, "-m", "alembic", action, target]
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                text=True, timeout=120)
        results.append({"command": command, "returncode": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            break
    artifact = OUTPUT / f"validation/migrations-{name}.json"
    artifact.write_text(json.dumps({"database": name, "results": results}, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "artifact": str(artifact), "returncodes": [r["returncode"] for r in results]
    }))
    if len(results) != 3 or any(r["returncode"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
