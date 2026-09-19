from evals.checks import parse_json, run_checks

EXPECTED = {"category": "billing", "priority": "high", "needs_human": True}


def test_rejects_prose_around_json():
    assert parse_json('Here you go: {"category": "billing"}') is None


def test_all_checks_pass_on_good_output():
    output = {"category": "billing", "priority": "high", "needs_human": True,
              "reply": "Sorry about the double charge. A teammate will review your account and follow up."}
    assert all(run_checks(output, EXPECTED).values())


def test_flags_card_number_in_reply():
    output = {"category": "billing", "priority": "high", "needs_human": True,
              "reply": "We received card 4111 1111 1111 1111."}
    assert run_checks(output, EXPECTED)["no_card_number_in_reply"] is False


def test_flags_promise_in_reply():
    output = {"category": "billing", "priority": "high", "needs_human": True,
              "reply": "Good news, we will refund you today!"}
    assert run_checks(output, EXPECTED)["no_promises_in_reply"] is False


def test_invalid_json_short_circuits():
    assert run_checks(None, EXPECTED) == {"valid_json": False}
