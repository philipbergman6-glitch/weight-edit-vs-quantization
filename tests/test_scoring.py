from wevq.scoring import answer_text, last_boxed, score_response


def test_normal_answer_after_closed_thinking_is_correct():
    f = score_response("Let me think. 2+2=4.\n</think>\n\nThe answer is \\boxed{4}.", False, "4")
    assert (f.looping, f.has_answer, f.looping_without_answer, f.correct) == (False, True, False, True)


def test_last_of_several_boxed_answers_wins():
    f = score_response("</think>First \\boxed{3}, on reflection \\boxed{5}.", False, "5")
    assert f.predicted == "5" and f.correct


def test_wrong_answer_is_not_correct():
    assert not score_response("</think>\\boxed{7}", False, "4").correct


def test_nested_braces_are_matched():
    assert last_boxed("so \\boxed{\\frac{1}{2}} done") == "\\frac{1}{2}"


def test_equivalent_forms_are_accepted():
    assert score_response("</think>\\boxed{0.5}", False, "\\frac{1}{2}").correct


def test_no_boxed_answer_means_no_answer_and_not_correct():
    f = score_response("</think>I think it is four.", False, "4")
    assert (f.has_answer, f.correct, f.predicted) == (False, False, None)


def test_unclosed_last_box_is_no_answer():
    assert last_boxed("earlier \\boxed{4} then \\boxed{\\frac{1}{2") is None


def test_boxed_inside_thinking_is_ignored_once_thinking_closes():
    f = score_response("maybe \\boxed{9}</think>The answer is 4.", False, "9")
    assert not f.has_answer


def test_thinking_never_closed_searches_the_whole_text():
    assert answer_text("still thinking \\boxed{4}") == "still thinking \\boxed{4}"
    assert score_response("still thinking \\boxed{4}", True, "4").correct


def test_cut_at_limit_without_answer_is_looping_without_answer():
    f = score_response("check that. check that. check that.", True, "4")
    assert (f.looping, f.looping_without_answer, f.correct) == (True, True, False)


def test_cut_at_limit_with_earlier_answer_is_looping_but_has_answer():
    f = score_response("</think>\\boxed{4}. Let me check. Let me check.", True, "4")
    assert (f.looping, f.has_answer, f.looping_without_answer, f.correct) == (True, True, False, True)
