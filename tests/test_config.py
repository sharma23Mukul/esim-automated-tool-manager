"""Tests for esim_toolmanager.core.config."""

from __future__ import annotations

from esim_toolmanager.core.config import ConfigManager


class TestConfigManager:
    def test_load_nonexistent_uses_defaults(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "nope.yaml")
        cfg.load()
        assert cfg.get("esim_version") == "2.5"

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "config.yaml"
        cfg = ConfigManager(config_path=path)
        cfg.set("esim_version", "3.0")
        cfg.save()
        assert path.exists()

        cfg2 = ConfigManager(config_path=path)
        cfg2.load()
        assert cfg2.get("esim_version") == "3.0"

    def test_dry_run_does_not_save(self, tmp_path):
        path = tmp_path / "config.yaml"
        cfg = ConfigManager(config_path=path, dry_run=True)
        cfg.set("key", "value")
        cfg.save()
        assert not path.exists()

    def test_set_get(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set("foo", "bar")
        assert cfg.get("foo") == "bar"
        assert cfg.get("missing", "default") == "default"

    def test_env_vars(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set_env_var("FOO", "/bar")
        assert cfg.get_env_vars() == {"FOO": "/bar"}

    def test_add_path_deduplication(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.add_path("/usr/bin")
        cfg.add_path("/usr/bin")
        cfg.add_path("/opt/bin")
        assert cfg.get_paths() == ["/usr/bin", "/opt/bin"]

    def test_export_env_script_bash(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set_env_var("TOOL_HOME", "/opt/tool")
        cfg.add_path("/opt/tool/bin")
        script = cfg.export_env_script("bash")
        assert 'export TOOL_HOME="/opt/tool"' in script
        assert "PATH" in script

    def test_export_env_script_powershell(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set_env_var("TOOL_HOME", "/opt/tool")
        script = cfg.export_env_script("powershell")
        assert '$env:TOOL_HOME = "/opt/tool"' in script

    def test_export_env_script_cmd(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set_env_var("TOOL_HOME", "/opt/tool")
        script = cfg.export_env_script("cmd")
        assert "SET TOOL_HOME=/opt/tool" in script

    def test_export_env_script_fish(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.set_env_var("X", "Y")
        script = cfg.export_env_script("fish")
        assert "set -gx" in script

    def test_export_env_script_unknown(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        script = cfg.export_env_script("unknown_shell")
        assert "Unsupported" in script

    def test_backup_creates_bak(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("esim_version: '2.5'\n")
        cfg = ConfigManager(config_path=path)
        bak = cfg.backup()
        assert bak is not None
        assert bak.suffix == ".bak"
        assert bak.exists()

    def test_backup_no_file_returns_none(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "nope.yaml")
        assert cfg.backup() is None

    def test_backup_dry_run(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("test\n")
        cfg = ConfigManager(config_path=path, dry_run=True)
        assert cfg.backup() is None

    def test_configure_tool(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        cfg.configure_tool("mock_tool", {
            "env_vars": {"MOCK_HOME": "/usr/share/mock"},
            "paths": ["/usr/bin"],
        })
        assert cfg.get_env_vars()["MOCK_HOME"] == "/usr/share/mock"
        assert "/usr/bin" in cfg.get_paths()
        tools_data = cfg.get("tools")
        assert tools_data["mock_tool"]["configured"] is True

    def test_data_property(self, tmp_path):
        cfg = ConfigManager(config_path=tmp_path / "c.yaml")
        d = cfg.data
        assert isinstance(d, dict)
        assert "esim_version" in d
