import os
import sys
import subprocess
import tempfile
import zipfile
import urllib.request
from pathlib import Path


class EmbeddedPostgres:
    def __init__(self):
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent

        self.base_dir = base_dir
        self.pg_root = self.base_dir / "embedded_pg"
        self.pg_bin = self.pg_root / "bin"
        self.pg_data = self.pg_root / "data"

        self.port = 5432
        self.username = "admin"
        self.password = "admin"
        self.database = "pos_network"

    def _has_binaries(self) -> bool:
        return (self.pg_bin / "postgres.exe").exists() and (self.pg_bin / "initdb.exe").exists()

    def ensure_binaries(self) -> bool:
        if self._has_binaries():
            return True

        try:
            self.pg_root.mkdir(parents=True, exist_ok=True)
            tmp_zip = Path(tempfile.gettempdir()) / "embedded_pg.zip"

            url = "https://get.enterprisedb.com/postgresql/postgresql-13.12-1-windows-x64-binaries.zip"

            urllib.request.urlretrieve(url, tmp_zip)

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(self.pg_root)

            if tmp_zip.exists():
                try:
                    tmp_zip.unlink()
                except Exception:
                    pass

            if not self._has_binaries():
                return False

            return True
        except Exception:
            return False

    def init_db(self) -> bool:
        if self.pg_data.exists():
            return True

        if not self._has_binaries():
            return False

        try:
            self.pg_data.mkdir(parents=True, exist_ok=True)

            cmd = [
                str(self.pg_bin / "initdb.exe"),
                "-D",
                str(self.pg_data),
                "-U",
                self.username,
                "--auth=md5",
                "--encoding=UTF8",
            ]

            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )

            return proc.returncode == 0
        except Exception:
            return False

    def start(self) -> bool:
        if not self._has_binaries() or not self.pg_data.exists():
            return False

        try:
            env = os.environ.copy()
            env["PATH"] = str(self.pg_bin) + os.pathsep + env.get("PATH", "")

            log_file = self.pg_root / "postgres.log"

            cmd = [
                str(self.pg_bin / "pg_ctl.exe"),
                "-D",
                str(self.pg_data),
                "-l",
                str(log_file),
                "-o",
                f"-p {self.port}",
                "start",
            ]

            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                timeout=60,
            )

            return True
        except Exception:
            return False

    def get_config(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "host": "localhost",
            "port": str(self.port),
            "database": self.database,
        }


def try_start_embedded_postgres() -> dict | None:
    try:
        ep = EmbeddedPostgres()
        if not ep.ensure_binaries():
            return None
        if not ep.init_db():
            return None
        if not ep.start():
            return None
        return ep.get_config()
    except Exception:
        return None
