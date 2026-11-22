"""Tests for esim_toolmanager.utils.version."""

from __future__ import annotations

from esim_toolmanager.utils.version import Version, parse_version, version_satisfies

# ── parse_version ────────────────────────────────────────────────────────────


class TestParseVersion:
    def test_semver(self):
        v = parse_version("1.2.3")
        assert v == Version(1, 2, 3)

    def test_major_only(self):
        v = parse_version("42")
        assert v == Version(42, 0, 0)

    def test_major_minor(self):
        v = parse_version("7.0")
        assert v == Version(7, 0, 0)

    def test_prerelease(self):
        v = parse_version("7.0.1-rc1")
        assert v is not None
        assert v.major == 7
        assert v.minor == 0
        assert v.patch == 1
        assert v.pre == "rc1"

    def test_embedded_in_text(self):
        v = parse_version("ngspice-42")
        assert v is not None
        assert v.major == 42

    def test_returns_none_on_garbage(self):
        assert parse_version("no-version-here") is None

    def test_returns_none_on_empty(self):
        assert parse_version("") is None

    def test_zero_version(self):
        v = parse_version("0.0.0")
        assert v == Version(0, 0, 0)


# ── Version comparison ──────────────────────────────────────────────────────


class TestVersionComparison:
    def test_less_than(self):
        assert Version(1, 0, 0) < Version(2, 0, 0)

    def test_greater_than(self):
        assert Version(2, 0, 0) > Version(1, 0, 0)

    def test_equal(self):
        assert Version(1, 2, 3) == Version(1, 2, 3)

    def test_not_equal(self):
        assert Version(1, 2, 3) != Version(1, 2, 4)

    def test_less_equal(self):
        assert Version(1, 2, 3) <= Version(1, 2, 3)
        assert Version(1, 2, 2) <= Version(1, 2, 3)

    def test_greater_equal(self):
        assert Version(1, 2, 3) >= Version(1, 2, 3)
        assert Version(1, 2, 4) >= Version(1, 2, 3)

    def test_minor_comparison(self):
        assert Version(1, 1, 0) < Version(1, 2, 0)

    def test_patch_comparison(self):
        assert Version(1, 2, 3) < Version(1, 2, 4)

    def test_str(self):
        assert str(Version(1, 2, 3)) == "1.2.3"
        assert str(Version(1, 2, 3, "rc1")) == "1.2.3-rc1"

    def test_repr(self):
        assert "Version" in repr(Version(1, 0, 0))

    def test_hash_equal_versions(self):
        assert hash(Version(1, 2, 3)) == hash(Version(1, 2, 3))

    def test_eq_non_version(self):
        assert Version(1, 0, 0).__eq__("not a version") is NotImplemented

    def test_lt_non_version(self):
        assert Version(1, 0, 0).__lt__("not a version") is NotImplemented


# ── version_satisfies ───────────────────────────────────────────────────────


class TestVersionSatisfies:
    def test_gte(self):
        assert version_satisfies(Version(2, 0, 0), ">=1.0") is True
        assert version_satisfies(Version(1, 0, 0), ">=1.0") is True
        assert version_satisfies(Version(0, 9, 0), ">=1.0") is False

    def test_lte(self):
        assert version_satisfies(Version(1, 0, 0), "<=2.0") is True
        assert version_satisfies(Version(3, 0, 0), "<=2.0") is False

    def test_eq(self):
        assert version_satisfies(Version(1, 0, 0), "==1.0") is True
        assert version_satisfies(Version(1, 0, 1), "==1.0") is False

    def test_neq(self):
        assert version_satisfies(Version(2, 0, 0), "!=1.0") is True
        assert version_satisfies(Version(1, 0, 0), "!=1.0") is False

    def test_gt(self):
        assert version_satisfies(Version(2, 0, 0), ">1.0") is True
        assert version_satisfies(Version(1, 0, 0), ">1.0") is False

    def test_lt(self):
        assert version_satisfies(Version(0, 9, 0), "<1.0") is True
        assert version_satisfies(Version(1, 0, 0), "<1.0") is False

    def test_compatible_release(self):
        # ~=1.5 → >=1.5, same major
        assert version_satisfies(Version(1, 6, 0), "~=1.5") is True
        assert version_satisfies(Version(1, 5, 0), "~=1.5") is True
        assert version_satisfies(Version(2, 0, 0), "~=1.5") is False
        assert version_satisfies(Version(1, 4, 0), "~=1.5") is False

    def test_bare_version_treated_as_gte(self):
        assert version_satisfies(Version(2, 0, 0), "1.0") is True
        assert version_satisfies(Version(0, 9, 0), "1.0") is False

    def test_invalid_constraint(self):
        assert version_satisfies(Version(1, 0, 0), "???") is False
