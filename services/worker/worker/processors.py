"""Pure job-processing functions. No I/O here, so they are trivial to unit test."""
from collections.abc import Callable
from typing import Any


def wordcount(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload["text"]
    words = text.split()
    return {
        "words": len(words),
        "characters": len(text),
        "unique_words": len({w.lower().strip(".,!?;:") for w in words}),
    }


def reverse(payload: dict[str, Any]) -> dict[str, Any]:
    return {"reversed": payload["text"][::-1]}


def fibonacci(payload: dict[str, Any]) -> dict[str, Any]:
    n = int(payload["n"])
    if n < 0:
        raise ValueError("n must be >= 0")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return {"n": n, "value": a}


def prime_check(payload: dict[str, Any]) -> dict[str, Any]:
    n = int(payload["n"])
    if n < 2:
        return {"n": n, "is_prime": False}
    if n % 2 == 0:
        return {"n": n, "is_prime": n == 2, **({"factor": 2} if n != 2 else {})}
    i = 3
    while i * i <= n:
        if n % i == 0:
            return {"n": n, "is_prime": False, "factor": i}
        i += 2
    return {"n": n, "is_prime": True}


PROCESSORS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "wordcount": wordcount,
    "reverse": reverse,
    "fibonacci": fibonacci,
    "prime_check": prime_check,
}


def process(job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        fn = PROCESSORS[job_type]
    except KeyError:
        raise ValueError(f"unsupported job type: {job_type}") from None
    return fn(payload)
