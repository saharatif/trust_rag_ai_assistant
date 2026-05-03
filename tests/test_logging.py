import json
import logging

from src.utils.logging import JsonFormatter, configure_logging


def test_json_formatter_produces_valid_json():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello world",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert "timestamp" in parsed


def test_json_formatter_includes_exception_info():
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="something failed",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "exception" in parsed
    assert "ValueError" in parsed["exception"]


def test_json_formatter_omits_exception_key_when_no_exc():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="no error",
        args=(),
        exc_info=None,
    )
    parsed = json.loads(formatter.format(record))
    assert "exception" not in parsed


def test_configure_logging_sets_level():
    configure_logging("WARNING")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    configure_logging("INFO")


def test_configure_logging_attaches_json_handler():
    configure_logging("INFO")
    root = logging.getLogger()
    assert len(root.handlers) >= 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_configure_logging_replaces_existing_handlers():
    root = logging.getLogger()
    # Add a dummy handler before calling configure
    dummy = logging.NullHandler()
    root.addHandler(dummy)
    handler_count_before = len(root.handlers)
    configure_logging("INFO")
    # After configure, only one StreamHandler should exist
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
