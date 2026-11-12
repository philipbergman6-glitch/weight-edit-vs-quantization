"""Turn one response into flags: looping, has a final answer, correct.

Follows the MIT authors' method (their `mathqa.py`, MIT licence): take the text
after the last `</think>`, find the last brace-matched `\\boxed{}` (or `\\fbox{}`),
and check it against the gold answer with math-verify. No model is called.
"""
from dataclasses import dataclass

from math_verify import parse, verify

THINK_END = "</think>"


def answer_text(response: str) -> str:
    """The part of the response after the last `</think>`; all of it if thinking never closed."""
    cut = response.rfind(THINK_END)
    return response if cut == -1 else response[cut + len(THINK_END):]


def last_boxed(text: str) -> str | None:
    """Contents of the last `\\boxed{...}` (else the last `\\fbox{...}`), brace matched; None if absent or unclosed."""
    start = text.rfind("\\boxed")
    if start == -1:
        start = text.rfind("\\fbox")
        if start == -1:
            return None
    open_brace = text.find("{", start)
    if open_brace == -1:
        return None
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace + 1:i]
    return None


def is_correct(gold: str, predicted: str) -> bool:
    """math-verify equivalence. Gold goes first (the check is not symmetric). Main thread only."""
    return bool(verify(parse(f"\\boxed{{{gold}}}"), parse(f"\\boxed{{{predicted}}}")))


@dataclass(frozen=True)
class Flags:
    looping: bool
    has_answer: bool
    looping_without_answer: bool
    correct: bool
    predicted: str | None


def score_response(response: str, hit_token_limit: bool, gold: str) -> Flags:
    predicted = last_boxed(answer_text(response))
    has_answer = predicted is not None
    return Flags(
        looping=hit_token_limit,
        has_answer=has_answer,
        looping_without_answer=hit_token_limit and not has_answer,
        correct=has_answer and is_correct(gold, predicted),
        predicted=predicted,
    )
