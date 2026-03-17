from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Iterable, TextIO


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

STARTUP_DELAY_SECONDS = 1.5
POLL_INTERVAL_SECONDS = 0.5
TERMINATE_TIMEOUT_SECONDS = 5


def print_message(message: str) -> None:
    print(message, flush=True)


def check_tool_availability(
    which: Callable[[str], str | None] = shutil.which,
    python_executable: str | None = None,
) -> list[str]:
    errors: list[str] = []
    active_python = python_executable or sys.executable

    if not active_python:
        errors.append("未检测到 Python 解释器，请使用 Python 运行 dev.py。")
    elif not Path(active_python).exists():
        errors.append(f"当前 Python 解释器不可用：{active_python}")

    if which("uv") is None:
        errors.append("未检测到 uv，请先安装 uv，并确认它已加入 PATH。")

    pnpm_exists = which("pnpm") is not None or which("pnpm.cmd") is not None
    if not pnpm_exists:
        errors.append("未检测到 pnpm，请先安装 pnpm，并确认它已加入 PATH。")

    return errors


def check_project_files(root: Path) -> list[str]:
    errors: list[str] = []
    required_files = {
        "后端依赖定义": root / "backend" / "pyproject.toml",
        "后端入口文件": root / "backend" / "app" / "main.py",
        "前端依赖定义": root / "frontend" / "package.json",
    }

    for label, file_path in required_files.items():
        if not file_path.exists():
            errors.append(f"{label}缺失：{file_path}")

    return errors


def check_dependency_state(root: Path) -> list[str]:
    errors: list[str] = []
    backend_venv = root / "backend" / ".venv"
    frontend_modules = root / "frontend" / "node_modules"

    if not backend_venv.exists():
        errors.append("后端依赖未准备完成，请先执行：cd backend && uv sync")

    if not frontend_modules.exists():
        errors.append("前端依赖未准备完成，请先执行：cd frontend && pnpm install")

    return errors


def resolve_pnpm_command() -> str:
    if os.name == "nt":
        return "pnpm.cmd"
    return "pnpm"


def build_commands() -> tuple[list[str], list[str]]:
    return ["uv", "run", "python", "-m", "app.main"], [resolve_pnpm_command(), "run", "dev"]


def stream_output(label: str, stream: TextIO | None) -> None:
    if stream is None:
        return

    try:
        for line in iter(stream.readline, ""):
            text = line.rstrip()
            if text:
                print_message(f"[{label}] {text}")
    finally:
        stream.close()


def start_process(label: str, command: list[str], cwd: Path) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")

    try:
        return subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"{label} 启动失败，命令不可执行：{' '.join(command)}") from exc
    except OSError as exc:
        raise RuntimeError(f"{label} 启动失败：{exc}") from exc


def terminate_process_tree(process: subprocess.Popen[str], label: str) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            process.terminate()
            process.wait(timeout=TERMINATE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
    except OSError as exc:
        print_message(f"[system] 结束 {label} 进程时出错：{exc}")


def report_errors(errors: Iterable[str]) -> None:
    for error in errors:
        print_message(f"[error] {error}")


def validate_environment(root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(check_tool_availability(python_executable=sys.executable))
    errors.extend(check_project_files(root))
    errors.extend(check_dependency_state(root))
    return errors


def main() -> int:
    errors = validate_environment(ROOT)
    if errors:
        report_errors(errors)
        return 1

    backend_command, frontend_command = build_commands()
    processes: dict[str, subprocess.Popen[str]] = {}
    log_threads: list[threading.Thread] = []

    try:
        print_message("[system] 启动后端服务...")
        backend_process = start_process("backend", backend_command, BACKEND_DIR)
        processes["backend"] = backend_process
        backend_thread = threading.Thread(
            target=stream_output,
            args=("backend", backend_process.stdout),
            daemon=True,
        )
        backend_thread.start()
        log_threads.append(backend_thread)

        time.sleep(STARTUP_DELAY_SECONDS)
        backend_return_code = backend_process.poll()
        if backend_return_code is not None and backend_return_code != 0:
            print_message(f"[error] backend 启动后立即退出，退出码：{backend_return_code}")
            return backend_return_code

        print_message("[system] 启动前端服务...")
        frontend_process = start_process("frontend", frontend_command, FRONTEND_DIR)
        processes["frontend"] = frontend_process
        frontend_thread = threading.Thread(
            target=stream_output,
            args=("frontend", frontend_process.stdout),
            daemon=True,
        )
        frontend_thread.start()
        log_threads.append(frontend_thread)

        time.sleep(STARTUP_DELAY_SECONDS)
        frontend_return_code = frontend_process.poll()
        if frontend_return_code is not None and frontend_return_code != 0:
            print_message(f"[error] frontend 启动后立即退出，退出码：{frontend_return_code}")
            return frontend_return_code

        print_message("[system] 前后端开发服务已启动，按 Ctrl+C 可统一退出。")

        while True:
            for label, process in processes.items():
                return_code = process.poll()
                if return_code is not None:
                    if return_code == 0:
                        print_message(f"[system] {label} 已退出。")
                    else:
                        print_message(f"[error] {label} 异常退出，退出码：{return_code}")
                    return return_code

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print_message("[system] 收到 Ctrl+C，正在关闭前后端进程...")
        return 0
    except RuntimeError as exc:
        print_message(f"[error] {exc}")
        return 1
    finally:
        for label, process in reversed(list(processes.items())):
            terminate_process_tree(process, label)

        for thread in log_threads:
            thread.join(timeout=1)


if __name__ == "__main__":
    raise SystemExit(main())