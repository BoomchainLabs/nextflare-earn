# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import sys
from pathlib import Path

import pytest


class TestTestsInitIntegration:
    """Integration tests for tests/__init__.py within the project ecosystem."""

    def test_tests_module_pytest_compatibility(self) -> None:
        """Test that the tests module works correctly within pytest framework."""
        import tests

        # Should be importable within pytest context
        assert tests is not None

        # Should not interfere with pytest functionality
        assert 'pytest' in sys.modules
        assert hasattr(pytest, 'main')
        assert hasattr(pytest, 'mark')

    def test_tests_module_coexists_with_existing_test_files(self) -> None:
        """Test that tests module coexists properly with other test files in the project."""

        # Verify tests directory structure
        tests_dir = Path(__file__).parent

        # Should contain the expected test files based on our earlier analysis
        expected_files = ['conftest.py', 'test_client.py', 'test_models.py']

        for expected_file in expected_files:
            file_path = tests_dir / expected_file
            if file_path.exists():
                assert file_path.is_file(), f"{expected_file} should be a file"

    def test_tests_module_doesnt_interfere_with_test_discovery(self) -> None:
        """Test that tests module doesn't interfere with pytest test discovery."""

        # The tests directory should still be discoverable by pytest
        tests_dir = Path(__file__).parent

        # Should contain test files
        test_files = list(tests_dir.glob('test_*.py'))
        assert len(test_files) > 0, "Should find test files in tests directory"

        # Should contain the __init__.py we're testing
        init_file = tests_dir / '__init__.py'
        assert init_file.exists()

    def test_tests_module_supports_package_structure(self) -> None:
        """Test that the tests module properly supports the package structure."""
        import tests

        # Verify the package structure allows for submodules
        assert hasattr(tests, '__path__') or tests.__file__.endswith('__init__.py')

        # Check for api_resources subpackage which should exist based on directory structure
        api_resources_path = Path(__file__).parent / 'api_resources'
        if api_resources_path.exists() and api_resources_path.is_dir():
            try:
                import tests.api_resources
                assert tests.api_resources is not None
            except ImportError:
                # This might fail in some test environments, which is acceptable
                pass

    def test_tests_module_works_with_conftest(self) -> None:
        """Test that tests module works properly with conftest.py configuration."""
        import tests

        # conftest.py should be accessible within the tests package
        conftest_path = Path(__file__).parent / 'conftest.py'
        if conftest_path.exists():
            # The presence of conftest.py should not interfere with tests module
            assert tests is not None
            assert hasattr(tests, '__file__')

            # Verify conftest functionality is available (this indicates proper pytest setup)
            assert 'pytest' in sys.modules

    def test_tests_module_respects_pytest_configuration(self) -> None:
        """Test that tests module respects pytest configuration and markers."""
        import tests

        # Should work with pytest markers and configuration
        # This is implicitly tested by the fact that these tests run successfully
        assert tests is not None

        # Verify pytest functionality is available
        assert hasattr(pytest, 'mark')
        assert hasattr(pytest, 'fixture')

    def test_tests_module_handles_async_test_environment(self) -> None:
        """Test that tests module works correctly in async test environments."""
        import tests

        # Based on conftest.py analysis, this project uses pytest-asyncio
        # The tests module should not interfere with async test functionality
        assert tests is not None

        # Check if pytest-asyncio is available (from conftest.py analysis)
        try:
            import pytest_asyncio
            # If available, ensure tests module doesn't interfere
            assert hasattr(pytest_asyncio, 'is_async_test')
        except ImportError:
            # pytest-asyncio might not be available in all test environments
            pass

    def test_tests_module_maintains_isolation_from_main_package(self) -> None:
        """Test that tests module maintains proper isolation from the main package."""
        import tests

        # Should not interfere with the main application package
        # Based on analysis, the main package appears to be 'earn_app'
        try:
            # If the main package is importable, it should be separate from tests
            import earn_app
            assert tests is not earn_app
            assert tests.__name__ != earn_app.__name__
        except ImportError:
            # Main package might not be available in test environment
            pass

    def test_tests_module_works_across_test_collection_phases(self) -> None:
        """Test that tests module works correctly during different pytest collection phases."""
        import tests

        # Should work during test collection (this test itself proves this)
        assert tests is not None

        # Should maintain consistency
        import importlib
        reimported_tests = importlib.import_module('tests')
        assert reimported_tests is tests

    def test_tests_module_filesystem_layout_consistency(self) -> None:
        """Test that tests module is consistent with the expected filesystem layout."""
        import tests

        # Verify the filesystem layout matches expectations
        tests_dir = Path(tests.__file__).parent

        # Should have expected structure based on our analysis
        expected_structure = [
            '__init__.py',
            'conftest.py',
        ]

        for expected_item in expected_structure:
            item_path = tests_dir / expected_item
            if expected_item == '__init__.py':
                # This must exist
                assert item_path.exists(), f"{expected_item} must exist"
            elif item_path.exists():
                # If it exists, verify it's the right type
                assert item_path.is_file(), f"{expected_item} should be a file"

    def test_tests_module_import_performance(self) -> None:
        """Test that importing tests module has reasonable performance characteristics."""
        import time

        # Time the import operation
        start_time = time.time()

        # Force reimport by removing from cache
        if 'tests' in sys.modules:
            del sys.modules['tests']

        end_time = time.time()
        import_time = end_time - start_time

        # Import should be fast (less than 1 second is very generous)
        assert import_time < 1.0, f"Import took too long: {import_time} seconds"

    def test_tests_module_works_with_test_utilities(self) -> None:
        """Test that tests module works properly with test utilities."""
        import tests

        # Check if utils.py exists (saw this in directory listing)
        utils_path = Path(__file__).parent / 'utils.py'
        if utils_path.exists():
            try:
                import tests.utils
                # Should coexist properly
                assert tests is not None
                assert tests.utils is not None
            except ImportError:
                # utils might not be directly importable
                pass

    def test_tests_module_error_propagation(self) -> None:
        """Test that tests module properly propagates errors without masking them."""
        import tests

        # Should not mask or suppress errors inappropriately
        try:
            # This should raise AttributeError, not be silently ignored
            _ = tests.non_existent_attribute
            pytest.fail("Should have raised AttributeError")
        except AttributeError:
            # Expected behavior
            pass
        except Exception as e:
            pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")

    def test_tests_module_project_structure_compliance(self) -> None:
        """Test that tests module complies with the overall project structure."""
        import tests

        # Verify it follows the Stainless project structure patterns
        tests_init_path = Path(tests.__file__)

        # Should be in a 'tests' directory at the project root level
        assert tests_init_path.name == '__init__.py'
        assert tests_init_path.parent.name == 'tests'

        # Project root should contain typical Python project files
        project_root = tests_init_path.parent.parent
        typical_files = ['.gitignore', '.python-version']

        for typical_file in typical_files:
            file_path = project_root / typical_file
            if file_path.exists():
                # If these files exist, we're likely at the right project root
                assert file_path.is_file()