"""
Simple example tests for validating test mode functionality.
"""


def test_basic_math():
    """Test basic arithmetic."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string_operations():
    """Test string operations."""
    result = "Hello, " + "World!"
    assert result == "Hello, World!"
    assert len(result) == 13


def test_list_operations():
    """Test list operations."""
    items = [1, 2, 3]
    items.append(4)
    assert len(items) == 4
    assert items[-1] == 4
