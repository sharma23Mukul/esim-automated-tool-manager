"""Tests for esim_toolmanager.backends."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from esim_toolmanager.backends import get_backend
from esim_toolmanager.backends.apt import AptBackend
from esim_toolmanager.backends.base import PackageBackend
from esim_toolmanager.backends.brew import BrewBackend
from esim_toolmanager.backends.choco import ChocoBackend
from esim_toolmanager.backends.pip_backend import PipBackend


class TestBaseBackend:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            PackageBackend()  # type: ignore[abstract]

    def test_repr(self):
        b = AptBackend(dry_run=True)
        assert "AptBackend" in repr(b)
        assert "dry_run=True" in repr(b)


class TestGetBackend:
    def test_known_backend(self):
        b = get_backend("apt", dry_run=True)
        assert isinstance(b, AptBackend)
        assert b.dry_run is True

    def test_unknown_backend(self):
        with pytest.raises(KeyError):
            get_backend("nonexistent")


class TestAptBackend:
    def test_name(self):
        assert AptBackend().name == "apt"

    @patch("esim_toolmanager.backends.apt.find_executable", return_value=None)
    def test_not_available(self, _mock):
        assert AptBackend().is_available() is False

    @patch("esim_toolmanager.backends.apt.find_executable", return_value="/usr/bin/apt-get")
    def test_available(self, _mock):
        assert AptBackend().is_available() is True

    @patch("esim_toolmanager.backends.apt.run_command", return_value=None)
    def test_install_dry_run(self, mock_run):
        b = AptBackend(dry_run=True)
        assert b.install("pkg") is True
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["dry_run"] is True

    @patch("esim_toolmanager.backends.apt.run_command")
    def test_is_installed_true(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert AptBackend().is_installed("pkg") is True

    @patch("esim_toolmanager.backends.apt.run_command")
    def test_is_installed_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        assert AptBackend().is_installed("pkg") is False

    @patch("esim_toolmanager.backends.apt.run_command")
    def test_get_installed_version(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="1.2.3")
        assert AptBackend().get_installed_version("pkg") == "1.2.3"

    @patch("esim_toolmanager.backends.apt.run_command")
    def test_get_installed_version_not_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert AptBackend().get_installed_version("pkg") is None

    @patch("esim_toolmanager.backends.apt.run_command", return_value=None)
    def test_update_index_dry_run(self, mock_run):
        b = AptBackend(dry_run=True)
        assert b.update_index() is True


class TestBrewBackend:
    def test_name(self):
        assert BrewBackend().name == "brew"

    @patch("esim_toolmanager.backends.brew.find_executable", return_value=None)
    def test_not_available(self, _mock):
        assert BrewBackend().is_available() is False

    @patch("esim_toolmanager.backends.brew.run_command", return_value=None)
    def test_install_dry_run(self, mock_run):
        b = BrewBackend(dry_run=True)
        assert b.install("pkg") is True

    @patch("esim_toolmanager.backends.brew.run_command")
    def test_get_installed_version(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="pkg 4.5.6")
        assert BrewBackend().get_installed_version("pkg") == "4.5.6"


class TestChocoBackend:
    def test_name(self):
        assert ChocoBackend().name == "choco"

    @patch("esim_toolmanager.backends.choco.find_executable", return_value=None)
    def test_not_available(self, _mock):
        assert ChocoBackend().is_available() is False

    @patch("esim_toolmanager.backends.choco.run_command", return_value=None)
    def test_install_dry_run(self, mock_run):
        b = ChocoBackend(dry_run=True)
        assert b.install("pkg") is True

    @patch("esim_toolmanager.backends.choco.run_command")
    def test_is_installed(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="pkg 1.0\n1 packages installed.")
        assert ChocoBackend().is_installed("pkg") is True

    @patch("esim_toolmanager.backends.choco.run_command")
    def test_get_installed_version(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="pkg 1.2.3\n1 packages installed.")
        assert ChocoBackend().get_installed_version("pkg") == "1.2.3"


class TestPipBackend:
    def test_name(self):
        assert PipBackend().name == "pip"

    @patch("esim_toolmanager.backends.pip_backend.run_command")
    def test_is_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        assert PipBackend().is_available() is True

    @patch("esim_toolmanager.backends.pip_backend.run_command")
    def test_get_installed_version(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Name: pkg\nVersion: 2.3.4\nSummary: test\n"
        )
        assert PipBackend().get_installed_version("pkg") == "2.3.4"

    @patch("esim_toolmanager.backends.pip_backend.run_command", return_value=None)
    def test_install_dry_run(self, mock_run):
        b = PipBackend(dry_run=True)
        assert b.install("pkg") is True
