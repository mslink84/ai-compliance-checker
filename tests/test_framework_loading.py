"""Tests for framework JSON loading."""

import pytest
from analyzer import FRAMEWORK_FILES, load_framework


def test_all_framework_files_exist():
    for name, path in FRAMEWORK_FILES.items():
        assert path.exists(), f"Framework file missing for {name}: {path}"


@pytest.mark.parametrize("name", ["GDPR", "ISO 27001", "NIST CSF 2.0"])
def test_framework_has_required_keys(name):
    fw = load_framework(name)
    assert "name" in fw
    assert "full_name" in fw
    assert "requirements" in fw
    assert len(fw["requirements"]) > 0


@pytest.mark.parametrize("name", ["GDPR", "ISO 27001", "NIST CSF 2.0"])
def test_requirements_have_required_fields(name):
    fw = load_framework(name)
    for req in fw["requirements"]:
        assert "id" in req, f"Missing 'id' in {name} requirement"
        assert "name" in req, f"Missing 'name' in {name} requirement"
        assert "description" in req, f"Missing 'description' in {name} requirement"
        assert "keywords" in req, f"Missing 'keywords' in {name} requirement"
        assert isinstance(req["keywords"], list), f"'keywords' must be a list in {name}"


def test_iso27001_a8_split():
    """ISO A8 must be split into three sub-requirements."""
    fw = load_framework("ISO 27001")
    ids = {req["id"] for req in fw["requirements"]}
    assert "ISO-A8-Access"     in ids, "ISO-A8-Access requirement missing"
    assert "ISO-A8-Vuln"       in ids, "ISO-A8-Vuln requirement missing"
    assert "ISO-A8-Monitoring" in ids, "ISO-A8-Monitoring requirement missing"
    assert "ISO-A8"            not in ids, "Old undivided ISO-A8 should not exist"


def test_unknown_framework_raises():
    with pytest.raises(KeyError):
        load_framework("Unknown Framework XYZ")
