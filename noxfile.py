"""Nox sessions."""
import shutil
import sys
from pathlib import Path
from textwrap import dedent

import nox
from nox.sessions import Session


package = "nldi_xstool"
python_versions = ["3.9"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = (
    "pre-commit",
    "safety",
    "mypy",
    "tests",
    "typeguard",
    "xdoctest",
    "docs-build",
)


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    if session.bin is None:
        return

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        text = hook.read_text()
        bindir = repr(session.bin)[1:-1]  # strip quotes
        if not (
            Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text
        ):
            continue

        lines = text.splitlines()
        if not (lines[0].startswith("#!") and "python" in lines[0].lower()):
            continue

        header = dedent(
            f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """
        )

        lines.insert(1, header)
        hook.write_text("\n".join(lines))


@nox.session(name="pre-commit", python="3.9", venv_backend="conda")
def precommit(session: Session) -> None:
    """Lint using pre-commit."""
    args = session.posargs or ["run", "--all-files", "--show-diff-on-failure"]
    session.conda_install(
        "--channel=conda-forge",
        "black",
        "darglint",
        "flake8",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "pep8-naming",
        "pre-commit",
    )
    session.install("flake8-bandit", "reorder-python-imports", "pre-commit-hooks")
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@nox.session(python="3.9", venv_backend="conda")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    session.conda_install("--channel=conda-forge", "safety")
    session.install(".")
    session.run("safety", "check", "--full-report")


@nox.session(python=python_versions, venv_backend="conda")
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or ["src", "tests", "docs/conf.py"]
    session.conda_install("--channel=conda-forge", "mypy", "pytest", "types-requests")
    session.install(".")
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@nox.session(python=python_versions, venv_backend="conda")
def tests(session: Session) -> None:
    """Run the test suite."""
    session.conda_install(
        "--channel=conda-forge",
        "toml",
        "coverage[toml]",
        "pytest",
        "pygments",
        "numpy>=1.21.0",
    )
    session.install(".")
    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@nox.session(python=python_versions, venv_backend="conda")
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.conda_install("--channel=conda-forge", "toml", "coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@nox.session(python=python_versions, venv_backend="conda")
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    session.conda_install(
        "--channel=conda-forge", "pytest", "typeguard", "pygments", "numpy>=1.21.0"
    )
    session.install(".")
    session.run("pytest", f"--typeguard-packages={package}", *session.posargs)


@nox.session(python=python_versions, venv_backend="conda")
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.conda_install("--channel=conda-forge", "xdoctest[colors]")
    session.install(".")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(name="docs-build", python="3.9", venv_backend="conda")
def docs_build(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    session.conda_install("--channel=conda-forge", "sphinx", "sphinx-click")
    session.install("sphinx-rtd-theme")
    session.install(".")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@nox.session(python="3.9", venv_backend="conda")
def docs(session: Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build"]
    session.conda_install(
        "--channel=conda-forge",
        "sphinx",
        "sphinx-autobuild",
        "sphinx-click",
    )
    session.install("sphinx-rtd-theme")
    session.install(".")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
