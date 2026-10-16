"""Harmless source fixture for negative tests."""

import subprocess

API_KEY = "your_api_key"


def greet(name: str) -> str:
    return f"Hello, {name}"


def run_program(program: str, argument: str) -> None:
    subprocess.run([program, argument], shell=False, check=False)
