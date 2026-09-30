import subprocess
from unittest.mock import patch

import pytest

from evidence import collect_dns


def test_dns_success():
    output = (
        ";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\n"
        ";; ANSWER SECTION:\n"
        "example.com. 60 IN A 192.0.2.20\n"
        "example.com. 60 IN A 192.0.2.10\n"
        "example.com. 60 IN A 192.0.2.20\n"
        "\n"
        ";; ADDITIONAL SECTION:\n"
        "other.example. 60 IN A 192.0.2.99\n"
    )
    completed = subprocess.CompletedProcess(
        args=["dig"], returncode=0, stdout=output, stderr=""
    )

    with patch("evidence.subprocess.run", return_value=completed) as run:
        record = collect_dns("example.com")

    assert record.check_type == "dns"
    assert record.target == "example.com"
    assert record.collected_at > 0
    assert record.result["status"] == "success"
    assert record.result["dns_status"] == "NOERROR"
    assert record.result["addresses"] == ["192.0.2.10", "192.0.2.20"]
    assert run.call_args.kwargs["timeout"] == 3


@pytest.mark.parametrize(
    "dns_status, expected_status",
    [
        ("NOERROR", "no_answer"),
        ("NXDOMAIN", "nxdomain"),
        ("SERVFAIL", "dns_error"),
        ("REFUSED", "dns_error"),
    ],
)
def test_dns_without_addresses(dns_status, expected_status):
    output = (
        f";; ->>HEADER<<- opcode: QUERY, status: {dns_status}, id: 1\n"
    )
    completed = subprocess.CompletedProcess(
        args=["dig"], returncode=0, stdout=output, stderr=""
    )

    with patch("evidence.subprocess.run", return_value=completed):
        record = collect_dns("example.com")

    assert record.result["status"] == expected_status
    assert record.result["dns_status"] == dns_status
    assert record.result["addresses"] == []


def test_dns_process_timeout():
    error = subprocess.TimeoutExpired(cmd=["dig"], timeout=3)

    with patch("evidence.subprocess.run", side_effect=error):
        record = collect_dns("example.com")

    assert record.result["status"] == "timeout"
    assert record.result["returncode"] is None


def test_dns_command_missing():
    with patch(
        "evidence.subprocess.run",
        side_effect=FileNotFoundError("dig not found"),
    ):
        record = collect_dns("example.com")

    assert record.result["status"] == "error"
    assert "dig not found" in record.result["stderr"]


@pytest.mark.parametrize("returncode", [0, 9])
def test_dns_missing_response_header(returncode):
    completed = subprocess.CompletedProcess(
        args=["dig"],
        returncode=returncode,
        stdout="No usable DNS response",
        stderr="",
    )

    with patch("evidence.subprocess.run", return_value=completed):
        record = collect_dns("example.com")

    assert record.result["status"] == "error"
    assert record.result["dns_status"] is None


@pytest.mark.parametrize("target", ["", "-bad.com", "a..com", None])
def test_dns_invalid_target(target):
    with patch("evidence.subprocess.run") as run:
        with pytest.raises(ValueError):
            collect_dns(target)

    run.assert_not_called()


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5])
def test_dns_invalid_timeout(timeout):
    with patch("evidence.subprocess.run") as run:
        with pytest.raises(ValueError):
            collect_dns("example.com", timeout=timeout)

    run.assert_not_called()
