import nox


@nox.session(reuse_venv=True, name="test-pydantic-v1")
def test_pydantic_v1(session: nox.Session) -> None:
    """
    Run tests using pytest with Pydantic version 1.x installed.
    
    This session installs development dependencies and Pydantic with a version constraint below 2, then executes pytest while excluding the 'tests/functional' directory. Any additional arguments provided to the session are forwarded to pytest.
    """
    session.install("-r", "requirements-dev.lock")
    session.install("pydantic<2")

    session.run("pytest", "--showlocals", "--ignore=tests/functional", *session.posargs)
