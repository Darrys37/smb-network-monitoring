import subprocess
from unittest.mock import patch

import pytest

from evidence import collect_ping, collect_tcp

@pytest.mark.parametrize(
    "returncode, expected_status",
    [
        (0, "success"),
        (1, "no_reply"),
        (2, "error"),
    ],
)
def test_ping_return_codes(returncode, expected_status):
    completed = subprocess.CompletedProcess(
        args=["ping"],
        returncode=returncode,
        stdout="sample output",
        stderr="",
    )

    with patch("evidence.subprocess.run", return_value=completed) as run:
        record = collect_ping("192.168.56.20")

    assert record.check_type == "ping"
    assert record.target == "192.168.56.20"
    assert record.collected_at > 0
    assert record.result["status"] == expected_status
    assert record.result["returncode"] == returncode
    assert record.result["stdout"] == "sample output"
    assert record.result["duration_ms"] >= 0
    assert run.call_args.kwargs["timeout"] == 3


def test_ping_process_timeout():
    error = subprocess.TimeoutExpired(cmd=["ping"], timeout=3)

    with patch("evidence.subprocess.run", side_effect=error):
        record = collect_ping("192.168.56.20")

    assert record.result["status"] == "timeout"
    assert record.result["returncode"] is None


def test_ping_command_missing():
    with patch(
        "evidence.subprocess.run",
        side_effect=FileNotFoundError("ping not found"),
    ):
        record = collect_ping("192.168.56.20")

    assert record.result["status"] == "error"
    assert "ping not found" in record.result["stderr"]


def test_ping_invalid_ip():
    with patch("evidence.subprocess.run") as run:
        with pytest.raises(ValueError):
            collect_ping("not-an-ip")

    run.assert_not_called()


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5])
def test_ping_invalid_timeout(timeout):
    with patch("evidence.subprocess.run") as run:
        with pytest.raises(ValueError):
            collect_ping("192.168.56.20", timeout=timeout)

    run.assert_not_called()
def test_tcp_success():
    with patch("evidence.socket.create_connection") as connect:
        record = collect_tcp("192.168.56.20", 80)

    connect.assert_called_once_with(
        ("192.168.56.20", 80), timeout=2
    )
    assert record.check_type == "tcp"
    assert record.target == "192.168.56.20"
    assert record.collected_at > 0
    assert record.result["port"] == 80
    assert record.result["status"] == "success"
    assert record.result["duration_ms"] >= 0


@pytest.mark.parametrize(
    "error, expected_status",
    [
        (ConnectionRefusedError(111, "Connection refused"), "refused"),
        (TimeoutError("Connection timed out"), "timeout"),
        (OSError(101, "Network is unreachable"), "error"),
    ],
)
def test_tcp_connection_errors(error, expected_status):
    with patch(
        "evidence.socket.create_connection",
        side_effect=error,
    ):
        record = collect_tcp("192.168.56.20", 80)

    assert record.result["status"] == expected_status
    assert record.result["error"] == str(error)
    assert record.result["errno"] == error.errno


@pytest.mark.parametrize("port", [0, 65536, True, "80"])
def test_tcp_invalid_port(port):
    with patch("evidence.socket.create_connection") as connect:
        with pytest.raises(ValueError):
            collect_tcp("192.168.56.20", port)

    connect.assert_not_called()


def test_tcp_invalid_ip():
    with patch("evidence.socket.create_connection") as connect:
        with pytest.raises(ValueError):
            collect_tcp("not-an-ip", 80)

    connect.assert_not_called()


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5])
def test_tcp_invalid_timeout(timeout):
    with patch("evidence.socket.create_connection") as connect:
        with pytest.raises(ValueError):
            collect_tcp("192.168.56.20", 80, timeout=timeout)

    connect.assert_not_called()
