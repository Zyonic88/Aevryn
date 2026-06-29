from __future__ import annotations

from pathlib import Path

from aevryn.security.secret_scan import scan_paths, scan_text, tracked_files

ROOT = Path(__file__).resolve().parents[1]


def test_secret_scan_detects_realistic_api_key_without_revealing_value() -> None:
    secret = "sk-" + "abcdefghijklmnopqrstuvwxyz1234567890"

    findings = scan_text("example.py", f'OPENAI_API_KEY="{secret}"\n')

    assert len(findings) == 1
    assert findings[0].rule_id == "openai_api_key"
    assert "<redacted>" in findings[0].snippet
    assert secret not in findings[0].snippet


def test_secret_scan_ignores_documented_placeholders() -> None:
    text = "\n".join(
        [
            "AEVRYN_OPENAI_API_KEY=...",
            "secret-provider-key",
            "sk-aevryn-test-secret-do-not-log",
            "API_KEY=local-dev-key",
        ]
    )

    assert scan_text("docs/example.md", text) == ()


def test_secret_scan_detects_private_keys_and_cloud_access_keys() -> None:
    text = "\n".join(
        [
            "-----BEGIN " + "PRIVATE KEY-----",
            "AKIA" + "ABCDEFGHIJKLMNOP",
        ]
    )

    findings = scan_text("keys.txt", text)

    assert {finding.rule_id for finding in findings} == {
        "aws_access_key_id",
        "private_key_block",
    }
    assert all("<redacted>" in finding.snippet for finding in findings)


def test_secret_scan_detects_generic_assigned_secrets() -> None:
    findings = scan_text("config.env", "SERVICE_TOKEN=abc123def456ghi789\n")

    assert len(findings) == 1
    assert findings[0].rule_id == "assigned_secret"
    assert "abc123def456ghi789" not in findings[0].snippet


def test_repository_secret_scan_tracked_files_pass() -> None:
    paths = tracked_files(ROOT)

    assert scan_paths(paths, root=ROOT) == ()
