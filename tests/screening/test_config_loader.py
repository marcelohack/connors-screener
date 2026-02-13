"""
Unit tests for screening configuration loader
"""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict

import pytest
import yaml

from connors_screener.core.screener import ScreeningConfig
from connors_screener.screening.config_loader import ScreeningConfigLoader


class TestScreeningConfigLoader:
    """Test configuration loader functionality"""

    @pytest.fixture
    def loader(self) -> ScreeningConfigLoader:
        """Create config loader instance"""
        return ScreeningConfigLoader()

    @pytest.fixture
    def sample_config_dict(self) -> Dict[str, Any]:
        """Sample configuration dictionary"""
        return {
            "name": "test_config",
            "provider": "tv",
            "description": "Test configuration",
            "parameters": {"rsi_level": 30, "volume_min": 1000000},
            "provider_config": {"volume_threshold": 1000000},
            "filters": [{"field": "RSI", "operation": "less", "value": 30}],
        }

    def test_create_config_from_dict(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test creating ScreeningConfig from dictionary"""
        config = loader._create_config_from_dict(sample_config_dict)

        assert isinstance(config, ScreeningConfig)
        assert config.name == "test_config"
        assert config.provider == "tv"
        assert config.description == "Test configuration"
        assert config.parameters["rsi_level"] == 30
        assert len(config.filters) == 1

    def test_create_config_missing_required_field(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Test error when required field is missing"""
        incomplete_config = {
            "name": "test",
            "provider": "tv",
            # Missing 'filters' field
        }

        with pytest.raises(ValueError, match="Missing required field 'filters'"):
            loader._create_config_from_dict(incomplete_config)

    def test_parse_single_config(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test parsing single configuration"""
        configs = loader._parse_config_data(sample_config_dict)

        assert len(configs) == 1
        assert configs[0].name == "test_config"

    def test_parse_multiple_configs(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test parsing multiple configurations"""
        multiple_configs = {
            "configurations": [
                sample_config_dict,
                {
                    "name": "test_config2",
                    "provider": "finviz",
                    "parameters": {},
                    "provider_config": {},
                    "filters": [{"field": "test", "operation": "eq", "value": 1}],
                },
            ]
        }

        configs = loader._parse_config_data(multiple_configs)

        assert len(configs) == 2
        assert configs[0].name == "test_config"
        assert configs[1].name == "test_config2"
        assert configs[1].provider == "finviz"

    def test_load_from_dict(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test loading from dictionary"""
        configs = loader.load_from_dict(sample_config_dict)

        assert len(configs) == 1
        assert configs[0].name == "test_config"

    def test_load_from_json_file(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test loading from JSON file"""
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config_dict, f)
            json_file = Path(f.name)

        try:
            configs = loader.load_from_file(json_file)

            assert len(configs) == 1
            assert configs[0].name == "test_config"
            assert configs[0].provider == "tv"
        finally:
            json_file.unlink()  # Clean up

    def test_load_from_yaml_file(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test loading from YAML file"""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_config_dict, f)
            yaml_file = Path(f.name)

        try:
            configs = loader.load_from_file(yaml_file)

            assert len(configs) == 1
            assert configs[0].name == "test_config"
            assert configs[0].provider == "tv"
        finally:
            yaml_file.unlink()  # Clean up

    def test_load_nonexistent_file(self, loader: ScreeningConfigLoader) -> None:
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            loader.load_from_file(Path("/nonexistent/file.json"))

    def test_load_unsupported_format(self, loader: ScreeningConfigLoader) -> None:
        """Test loading from unsupported file format"""
        with NamedTemporaryFile(suffix=".txt") as f:
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load_from_file(Path(f.name))

    def test_register_configs_from_file(
        self, loader: ScreeningConfigLoader, sample_config_dict: Dict[str, Any]
    ) -> None:
        """Test registering configurations from file"""
        from connors_core.core.registry import ComponentRegistry

        # Create fresh registry for this test
        test_registry = ComponentRegistry()

        # Mock registry to use our test instance
        import connors_screener.screening.config_loader

        original_registry = connors_screener.screening.config_loader.registry
        connors_screener.screening.config_loader.registry = test_registry

        try:
            with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(sample_config_dict, f)
                json_file = Path(f.name)

            registered_names = loader.register_configs_from_file(json_file)

            assert len(registered_names) == 1
            assert "tv:test_config" in registered_names

            # Verify config was registered
            retrieved_config = test_registry.get_screening_config("tv", "test_config")
            assert retrieved_config.name == "test_config"

        finally:
            # Restore original registry
            connors_screener.screening.config_loader.registry = original_registry
            json_file.unlink()  # Clean up

    def test_create_example_config_file_yaml(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Test creating example YAML configuration file"""
        with NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            example_file = Path(f.name)

        try:
            loader.create_example_config_file(example_file, "yaml")

            assert example_file.exists()

            # Load and verify content
            with open(example_file) as f:
                content = yaml.safe_load(f)

            assert "configurations" in content
            assert len(content["configurations"]) >= 2
            assert all(
                "name" in config and "provider" in config and "filters" in config
                for config in content["configurations"]
            )

        finally:
            if example_file.exists():
                example_file.unlink()  # Clean up

    def test_create_example_config_file_json(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Test creating example JSON configuration file"""
        with NamedTemporaryFile(suffix=".json", delete=False) as f:
            example_file = Path(f.name)

        try:
            loader.create_example_config_file(example_file, "json")

            assert example_file.exists()

            # Load and verify content
            with open(example_file) as f:
                content = json.load(f)

            assert "configurations" in content
            assert len(content["configurations"]) >= 2

        finally:
            if example_file.exists():
                example_file.unlink()  # Clean up

    def test_supported_formats(self, loader: ScreeningConfigLoader) -> None:
        """Test that loader supports expected formats"""
        expected_formats = {".json", ".yaml", ".yml"}
        assert loader.supported_formats == expected_formats


class TestConfigLoaderMetadata:
    """Tests for metadata-aware loading (post_filter / post_filter_context)"""

    @pytest.fixture
    def loader(self) -> ScreeningConfigLoader:
        return ScreeningConfigLoader()

    def test_extract_metadata_with_post_filter(self) -> None:
        """Extracts post_filter + context from a config dict"""
        cfg = {
            "name": "x",
            "provider": "tv",
            "filters": [],
            "post_filter": "elephant_bars",
            "post_filter_context": {"volume_multiplier": 3.0},
        }
        meta = ScreeningConfigLoader._extract_metadata_from_dict(cfg)
        assert meta == {
            "post_filter": "elephant_bars",
            "post_filter_context": {"volume_multiplier": 3.0},
        }

    def test_extract_metadata_empty_when_absent(self) -> None:
        """No metadata fields -> empty dict"""
        cfg = {"name": "x", "provider": "tv", "filters": []}
        meta = ScreeningConfigLoader._extract_metadata_from_dict(cfg)
        assert meta == {}

    def test_load_from_file_with_metadata_yaml(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Round-trip: YAML with metadata -> configs + metadata dict"""
        data = {
            "name": "eb",
            "provider": "tv",
            "filters": [{"field": "volume", "operation": "greater", "value": 100}],
            "post_filter": "elephant_bars",
            "post_filter_context": {"atr_multiplier": 2.0},
        }
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = Path(f.name)

        try:
            configs, meta = loader.load_from_file_with_metadata(path)
            assert len(configs) == 1
            assert configs[0].name == "eb"
            assert "eb" in meta
            assert meta["eb"]["post_filter"] == "elephant_bars"
            assert meta["eb"]["post_filter_context"]["atr_multiplier"] == 2.0
        finally:
            path.unlink()

    def test_load_multiple_configs_mixed_metadata(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Multi-config: only configs with metadata get entries"""
        data = {
            "configurations": [
                {
                    "name": "with_meta",
                    "provider": "tv",
                    "filters": [
                        {"field": "volume", "operation": "greater", "value": 1}
                    ],
                    "post_filter": "elephant_bars",
                },
                {
                    "name": "no_meta",
                    "provider": "tv",
                    "filters": [
                        {"field": "close", "operation": "greater", "value": 1}
                    ],
                },
            ]
        }
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = Path(f.name)

        try:
            configs, meta = loader.load_from_file_with_metadata(path)
            assert len(configs) == 2
            assert "with_meta" in meta
            assert "no_meta" not in meta
            assert meta["with_meta"]["post_filter"] == "elephant_bars"
        finally:
            path.unlink()

    def test_post_filter_fields_not_in_screening_config(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Metadata doesn't leak into ScreeningConfig attributes"""
        data = {
            "name": "leak_check",
            "provider": "tv",
            "filters": [{"field": "volume", "operation": "greater", "value": 1}],
            "post_filter": "elephant_bars",
            "post_filter_context": {"volume_multiplier": 3.0},
        }
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = Path(f.name)

        try:
            configs, meta = loader.load_from_file_with_metadata(path)
            config = configs[0]
            assert not hasattr(config, "post_filter")
            assert not hasattr(config, "post_filter_context")
            assert "post_filter" not in config.parameters
        finally:
            path.unlink()

    def test_register_configs_from_file_with_metadata(
        self, loader: ScreeningConfigLoader
    ) -> None:
        """Configs registered + metadata returned"""
        from connors_core.core.registry import ComponentRegistry

        test_registry = ComponentRegistry()

        import connors_screener.screening.config_loader

        original_registry = connors_screener.screening.config_loader.registry
        connors_screener.screening.config_loader.registry = test_registry

        try:
            data = {
                "name": "reg_meta",
                "provider": "tv",
                "filters": [
                    {"field": "volume", "operation": "greater", "value": 1}
                ],
                "post_filter": "elephant_bars",
                "post_filter_context": {"volume_multiplier": 3.0},
            }
            with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                yaml.dump(data, f)
                path = Path(f.name)

            names, meta = loader.register_configs_from_file_with_metadata(path)
            assert "tv:reg_meta" in names
            assert meta["reg_meta"]["post_filter"] == "elephant_bars"
            assert meta["reg_meta"]["post_filter_context"]["volume_multiplier"] == 3.0

            # Verify config was actually registered
            retrieved = test_registry.get_screening_config("tv", "reg_meta")
            assert retrieved.name == "reg_meta"
        finally:
            connors_screener.screening.config_loader.registry = original_registry
            path.unlink()
