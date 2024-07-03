"""Nox file for unit testing and linting."""

from pathlib import Path
import os
import nox


@nox.session()
def lint(session):
    """Run linter."""
    session.run("pip", "install", "ruff>=0.3.2")
    with open(Path(__file__).parent.resolve() / "flake8.report", "w", encoding="utf-8") as stdout:
        session.run("ruff", "check", "pl_parking", "-v", "--exit-zero", external=True, stdout=stdout)
