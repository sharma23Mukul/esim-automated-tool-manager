"""Tests for esim_toolmanager.platform.detect."""

from __future__ import annotations

from unittest.mock import mock_open, patch

from esim_toolmanager.platform.detect import PlatformInfo, _parse_os_release, detect_platform


class TestPlatformInfo:
    def test_package_manager_ubuntu(self):
        p = PlatformInfo("linux", "x86_64", "ubuntu", "22.04")
        assert p.package_manager == "apt"

    def test_package_manager_fedora(self):
        p = PlatformInfo("linux", "x86_64", "fedora", "39")
        assert p.package_manager == "dnf"

    @patch("shutil.which", return_value="/usr/local/bin/brew")
    def test_package_manager_macos(self, _mock):
        p = PlatformInfo("darwin", "arm64", "macos", "14.0")
        assert p.package_manager == "brew"

    @patch("shutil.which", side_effect=lambda x: "/bin/choco" if x == "choco" else None)
    def test_package_manager_windows_choco(self, _mock):
        p = PlatformInfo("windows", "x86_64", "windows", "10.0")
        assert p.package_manager == "choco"

    @patch("shutil.which", return_value=None)
    def test_package_manager_windows_none(self, _mock):
        p = PlatformInfo("windows", "x86_64", "windows", "10.0")
        assert p.package_manager is None

    @patch("shutil.which", return_value=None)
    def test_package_manager_unknown_linux(self, _mock):
        p = PlatformInfo("linux", "x86_64", "gentoo", "2.14")
        assert p.package_manager is None

    def test_is_linux(self):
        p = PlatformInfo("linux", "x86_64", "ubuntu", "22.04")
        assert p.is_linux is True
        assert p.is_windows is False
        assert p.is_macos is False

    def test_is_windows(self):
        p = PlatformInfo("windows", "x86_64", "windows", "10.0")
        assert p.is_windows is True
        assert p.is_linux is False

    def test_is_macos(self):
        p = PlatformInfo("darwin", "arm64", "macos", "14.0")
        assert p.is_macos is True


class TestDetectPlatform:
    @patch("esim_toolmanager.platform.detect._platform.system", return_value="Linux")
    @patch("esim_toolmanager.platform.detect._platform.machine", return_value="x86_64")
    @patch(
        "builtins.open",
        mock_open(read_data='ID=ubuntu\nVERSION_ID="22.04"\nNAME="Ubuntu"\n'),
    )
    def test_detect_linux(self, _m_machine, _m_sys):
        p = detect_platform()
        assert p.os_name == "linux"
        assert p.arch == "x86_64"
        assert p.distro == "ubuntu"
        assert p.distro_version == "22.04"

    @patch("esim_toolmanager.platform.detect._platform.system", return_value="Windows")
    @patch("esim_toolmanager.platform.detect._platform.machine", return_value="AMD64")
    @patch("esim_toolmanager.platform.detect._platform.version", return_value="10.0.19045")
    def test_detect_windows(self, _v, _m, _s):
        p = detect_platform()
        assert p.os_name == "windows"
        assert p.distro == "windows"

    @patch("esim_toolmanager.platform.detect._platform.system", return_value="Darwin")
    @patch("esim_toolmanager.platform.detect._platform.machine", return_value="arm64")
    @patch("esim_toolmanager.platform.detect._platform.mac_ver", return_value=("14.0", ("", "", ""), ""))
    def test_detect_macos(self, _mv, _m, _s):
        p = detect_platform()
        assert p.os_name == "darwin"
        assert p.distro == "macos"
        assert p.distro_version == "14.0"


class TestParseOsRelease:
    @patch("builtins.open", mock_open(read_data='ID=fedora\nVERSION_ID="39"\n'))
    def test_parse_fedora(self):
        distro, ver = _parse_os_release()
        assert distro == "fedora"
        assert ver == "39"

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found(self, _mock):
        distro, ver = _parse_os_release()
        assert distro == "unknown"
        assert ver == ""
