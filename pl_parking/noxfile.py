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


def check_init_files(directory):
    """Check that every directory has an __init__.py file."""
    missing_init_files = []
    for root, dirs, files in os.walk(directory):
        # Skip the root directory itself and __pycache__ directories
        if root == directory or "__pycache__" in root:
            continue

        if "__init__.py" not in files:
            missing_init_files.append(root)

    return missing_init_files


@nox.session()
def check_inits(session):
    """Check for missing __init__.py files in directories."""
    directory_to_check = "pl_parking"  # Adjust this to your top-level directory to check
    missing_init_files = check_init_files(directory_to_check)

    if missing_init_files:
        session.error(f"The following directories are missing an __init__.py file:\n" + "\n".join(missing_init_files))
    else:
        print("All directories contain an __init__.py file.")


@nox.session()
def pylint(session):
    """Run linter."""
    session.run("pip", "install", "pylint>=3.2.6")
    report_file = Path(__file__).parent.resolve() / "pylint.report"
    with open(Path(__file__).parent.resolve() / "pylint.report", "w", encoding="utf-8") as stdout:
        session.run("pylint", "pl_parking\\PLP", "--disable=all", "--enable=E1101", external=True, stdout=stdout)
    session.log(f"Pylint report saved to {report_file}")
