from __future__ import annotations

import pathlib
import shutil
import subprocess
import time
import typing as t

import nox
from nox import options

BACKEND_PATH = pathlib.Path(__file__).parent / "backend"
PYTHON_PATHS = [BACKEND_PATH, "noxfile.py"]
REFORMATTING_PATHS = PYTHON_PATHS


REFORMATTING_FILE_EXTS = (
    ".py",
    ".pyx",
    ".pyi",
    ".c",
    ".cpp",
    ".cxx",
    ".hpp",
    ".hxx",
    ".h",
    ".yml",
    ".yaml",
    ".html",
    ".htm",
    ".js",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".css",
    ".md",
    ".dockerfile",
    "Dockerfile",
    ".editorconfig",
    ".gitattributes",
    ".json",
    ".gitignore",
    ".dockerignore",
    ".txt",
    ".sh",
    ".bat",
    ".ps1",
    ".rb",
    ".pl",
)

GIT = shutil.which("git")

options.default_venv_backend = "uv"
options.sessions = ["pyright", "ruff"]


# uv_sync taken from: https://github.com/hikari-py/hikari/blob/master/pipelines/nox.py#L48
#
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
def uv_sync(
    session: nox.Session, /, *, include_self: bool = False, extras: t.Sequence[str] = (), groups: t.Sequence[str] = ()
) -> None:
    if extras and not include_self:
        raise RuntimeError("When specifying extras, set `include_self=True`.")

    args: list[str] = []
    for extra in extras:
        args.extend(("--extra", extra))

    group_flag = "--group" if include_self else "--only-group"
    for group in groups:
        args.extend((group_flag, group))

    session.run_install(
        "uv", "sync", "--frozen", *args, silent=True, env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    )


@nox.session(reuse_venv=True)
def ruff(session: nox.Session) -> None:
    uv_sync(session, groups=["dev", "ruff"])

    remove_trailing_whitespaces(session)

    session.run("python", "-m", "ruff", "format", *PYTHON_PATHS)
    session.run("python", "-m", "ruff", "check", *PYTHON_PATHS, "--fix")


@nox.session(reuse_venv=True)
def ruff_check(session: nox.Session) -> None:
    uv_sync(session, groups=["dev", "ruff"])

    session.run("python", "-m", "ruff", "format", *PYTHON_PATHS, "--check")
    session.run("python", "-m", "ruff", "check", *PYTHON_PATHS)


@nox.session(reuse_venv=True)
def pyright(session: nox.Session) -> None:
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pyright", *PYTHON_PATHS)


@nox.session(venv_backend="none")
def check_trailing_whitespaces(session: nox.Session) -> None:
    """Check for trailing whitespaces in the project."""
    remove_trailing_whitespaces(session, check_only=True)


def remove_trailing_whitespaces(session: nox.Session, /, *, check_only: bool = False) -> None:
    """Remove trailing whitespaces and ensure LR ends are being used."""
    session.log(f"Searching for stray trailing whitespaces in files ending in {REFORMATTING_FILE_EXTS}")

    count = 0
    total = 0

    start = time.perf_counter()
    for raw_path in REFORMATTING_PATHS:
        path = pathlib.Path(raw_path)

        dir_total, dir_count = _remove_trailing_whitespaces_for_directory(
            pathlib.Path(path), session, check_only=check_only
        )

        total += dir_total
        count += dir_count

    end = time.perf_counter()

    remark = "Good job! " if not count else ""
    message = "Had to fix" if not check_only else "Found issues in"
    call = session.error if check_only and count else session.log

    call(
        f"{message} {count} file(s). "
        f"{remark}Took {1_000 * (end - start):.2f}ms to check {total} files in this project."
        + ("\nTry running 'nox -s reformat-code' to fix them" if check_only and count else "")
    )


def _remove_trailing_whitespaces_for_directory(
    root_path: pathlib.Path, session: nox.Session, /, *, check_only: bool
) -> tuple[int, int]:
    total = 0
    count = 0

    for path in root_path.glob("*"):
        if path.is_file():
            if path.name.casefold().endswith(REFORMATTING_FILE_EXTS):
                total += 1
                count += _remove_trailing_whitespaces_for_file(path, session, check_only=check_only)
            continue

        dir_total, dir_count = _remove_trailing_whitespaces_for_directory(path, session, check_only=check_only)

        total += dir_total
        count += dir_count

    return total, count


def _remove_trailing_whitespaces_for_file(file: pathlib.Path, session: nox.Session, /, *, check_only: bool) -> bool:
    try:
        lines = file.read_bytes().splitlines(keepends=True)
        new_lines = lines.copy()

        for i in range(len(new_lines)):
            line = lines[i].rstrip(b"\n\r \t")
            line += b"\n"
            new_lines[i] = line

        if lines == new_lines:
            return False

        if check_only:
            session.warn(f"Trailing whitespaces found in {file}")
            return True

        session.log(f"Removing trailing whitespaces present in {file}")

        file.write_bytes(b"".join(lines))

        if GIT is not None:
            result = subprocess.check_call(  # noqa: S603
                [GIT, "add", file, "-vf"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None
            )
            assert result == 0, f"`git add {file} -v' exited with code {result}"

    except Exception as ex:  # noqa: BLE001
        session.warn("Failed to check", file, "because", type(ex).__name__, ex)

    return True
