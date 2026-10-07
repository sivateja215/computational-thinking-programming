from hypothesis import given, strategies as st


def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


def test_add():
    assert add(2, 3) == 5


def test_multiply():
    assert multiply(4, 5) == 20


@given(st.integers(), st.integers())
def test_add_property(a, b):
    assert add(a, b) == a + b


@given(st.integers(), st.integers())
def test_multiply_property(a, b):
    assert multiply(a, b) == a * b