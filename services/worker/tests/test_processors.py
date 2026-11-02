import pytest

from worker.processors import process

pytestmark = pytest.mark.unit


def test_wordcount():
    assert process("wordcount", {"text": "Hello hello world!"}) == {
        "words": 3, "characters": 18, "unique_words": 2,
    }


def test_reverse():
    assert process("reverse", {"text": "abc"}) == {"reversed": "cba"}


@pytest.mark.parametrize("n,expected", [(0, 0), (1, 1), (2, 1), (10, 55), (90, 2880067194370816120)])
def test_fibonacci(n, expected):
    assert process("fibonacci", {"n": n})["value"] == expected


def test_fibonacci_negative():
    with pytest.raises(ValueError):
        process("fibonacci", {"n": -1})


@pytest.mark.parametrize("n,is_prime", [(0, False), (1, False), (2, True), (3, True), (4, False),
                                        (97, True), (100, False), (7919, True), (1_000_000_007, True)])
def test_prime_check(n, is_prime):
    assert process("prime_check", {"n": n})["is_prime"] is is_prime


def test_prime_check_reports_factor():
    assert process("prime_check", {"n": 91})["factor"] == 7


def test_unknown_type():
    with pytest.raises(ValueError, match="unsupported"):
        process("nope", {})
