"""Synthetic static-analysis fixture. Do not execute this file."""

API_KEY = "NOT_A_REAL_SECRET_fixture_only_8492"


def review_user_expression(expression: str) -> object:
    # PRM should flag this dynamic code execution pattern.
    return eval(expression)  # noqa: S307 - intentional test fixture; do not execute


def run_command(command: str) -> None:
    import subprocess

    # PRM should flag shell=True as a command-injection risk pattern.
    subprocess.run(command, shell=True, check=False)  # noqa: S602 - fixture only
