import logging

from view import VIEW


def test_custom_formatter_with_extra_entities(capsys):
    """Test custom formatting used by VIEW object"""

    _view = VIEW()
    logger = logging.getLogger("VIEW")

    # Log messages with extra entities
    extra_context = {"user_id": 123, "session_id": "abc456"}

    logger.info("This is an info message", extra=extra_context)
    logger.warning("This is a warning message", extra=extra_context)
    logger.debug("This is a debug message", extra=extra_context)

    expected_line_endings = [
        "[VIEW] VIEW object initialized for offline use",
        "[VIEW] Context: {'Version': '1.4.dev110+gbed3da38c.d20260219'}",
        "[VIEW] This is an info message",
        "[VIEW] Context: {'user_id': 123, 'session_id': 'abc456'}",
        "[VIEW] This is a warning message",
        "[VIEW] Context: {'user_id': 123, 'session_id': 'abc456'}",
    ]

    captured = capsys.readouterr()

    captured_out_lines = captured.out.splitlines()

    for expected_line_ending, captured_line in zip(
        expected_line_endings, captured_out_lines, strict=True
    ):
        assert captured_line.endswith(expected_line_ending)
