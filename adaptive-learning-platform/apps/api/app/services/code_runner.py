from __future__ import annotations
import os
import socket
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class CodeRunResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    tests_passed: bool

    def to_dict(self) -> dict:
        return asdict(self)


class CodeRunner(ABC):
    @abstractmethod
    def run(self, code: str, visible_tests: str = "", hidden_tests: str = "") -> CodeRunResult: ...


class DockerCodeRunner(CodeRunner):
    def __init__(self, image: str = "python:3.13-alpine", timeout_seconds: int = 5, work_root: str | None = None, in_container: bool = False) -> None:
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.work_root = work_root
        self.in_container = in_container

    def command(self, directory: str) -> list[str]:
        mount = ["--volumes-from", f"{socket.gethostname()}:ro"] if self.in_container else ["-v", f"{directory}:/work:ro"]
        work_dir = directory if self.in_container else "/work"
        return [
            "docker", "run", "--rm", "--network", "none", "--cpus", "0.5",
            "--memory", "128m", "--pids-limit", "64", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", *mount,
            "-w", work_dir, self.image, "python", "submission.py",
        ]

    def run(self, code: str, visible_tests: str = "", hidden_tests: str = "") -> CodeRunResult:
        with tempfile.TemporaryDirectory(prefix="adaptive-code-", dir=self.work_root) as temp:
            path = Path(temp) / "submission.py"
            path.write_text(f"{code}\n\n{visible_tests}\n\n{hidden_tests}\n", encoding="utf-8")
            try:
                completed = subprocess.run(
                    self.command(temp), capture_output=True, text=True,
                    timeout=self.timeout_seconds, check=False, env={"PATH": os.environ.get("PATH", "")},
                )
                return CodeRunResult(completed.returncode, completed.stdout[-8000:], completed.stderr[-8000:], False, completed.returncode == 0)
            except subprocess.TimeoutExpired as exc:
                return CodeRunResult(None, (exc.stdout or "")[-8000:], "Execution timed out", True, False)
            except FileNotFoundError:
                return CodeRunResult(None, "", "Docker is unavailable. Learner code was not executed on the host.", False, False)
