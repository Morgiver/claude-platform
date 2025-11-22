"""Config loader - Load YAML configuration files with environment variable substitution."""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml


logger = logging.getLogger(__name__)


def _substitute_env_vars(data: Any) -> Any:
    """
    Recursively substitute environment variables in configuration data.

    Supports ${VAR_NAME} syntax. Missing environment variables use empty string
    with a warning log.

    Args:
        data: Configuration data (dict, list, str, or other)

    Returns:
        Data with environment variables substituted
    """
    if isinstance(data, dict):
        return {key: _substitute_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Find all ${VAR_NAME} patterns
        pattern = r'\$\{([^}]+)\}'

        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1)
            value = os.environ.get(var_name)

            if value is None:
                logger.warning(
                    f"Environment variable '${{{var_name}}}' not found, using empty string"
                )
                return ""

            return value

        return re.sub(pattern, replace_env_var, data)
    else:
        return data


def load_yaml_config(file_path: str | Path) -> Dict[str, Any]:
    """
    Load YAML configuration file with environment variable substitution.

    Supports ${VAR_NAME} syntax for environment variable substitution.
    Missing environment variables are replaced with empty string and log a warning.

    Args:
        file_path: Path to YAML configuration file

    Returns:
        Configuration dictionary with environment variables substituted

    Raises:
        FileNotFoundError: If configuration file does not exist
        yaml.YAMLError: If YAML file is invalid
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        error_msg = f"Configuration file not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Load YAML file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if config is None:
            logger.warning(f"Configuration file is empty: {file_path}")
            return {}

        logger.debug(f"Loaded configuration from: {file_path}")

    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML in {file_path}: {e}"
        logger.error(error_msg)
        raise yaml.YAMLError(error_msg) from e

    # Substitute environment variables
    config = _substitute_env_vars(config)

    return config


def load_all_configs(config_dir: Path = Path("config")) -> Dict[str, Any]:
    """
    Load all configuration files and merge them into a single configuration dictionary.

    Loads the following files:
    - main.yaml: Main application configuration
    - logging.yaml: Logging configuration (merged into config['logging'])
    - modules.yaml: Module declarations (merged into config['modules'])

    Args:
        config_dir: Directory containing configuration files. Defaults to ./config

    Returns:
        Combined configuration dictionary

    Raises:
        FileNotFoundError: If main.yaml is missing (required)
        yaml.YAMLError: If any YAML file is invalid
    """
    config_dir = Path(config_dir)

    if not config_dir.exists():
        error_msg = f"Configuration directory not found: {config_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Load main configuration (required)
    main_config_path = config_dir / "main.yaml"
    config = load_yaml_config(main_config_path)

    # Load logging configuration (optional - merge if exists)
    logging_config_path = config_dir / "logging.yaml"
    if logging_config_path.exists():
        try:
            logging_config = load_yaml_config(logging_config_path)
            # Merge logging config
            if 'logging' in logging_config:
                config['logging'] = logging_config['logging']
            logger.debug("Loaded logging configuration")
        except Exception as e:
            logger.warning(f"Failed to load logging config, using defaults: {e}")
    else:
        logger.debug(f"Logging config not found: {logging_config_path}, using defaults")

    # Load modules configuration (optional - merge if exists)
    modules_config_path = config_dir / "modules.yaml"
    if modules_config_path.exists():
        try:
            modules_config = load_yaml_config(modules_config_path)
            # Merge modules config
            if 'modules' not in config:
                config['modules'] = {}
            # modules.yaml contains { "modules": [...], "search_paths": [...] }
            # Merge each key separately
            for key, value in modules_config.items():
                config['modules'][key] = value
            logger.debug("Loaded modules configuration")
        except Exception as e:
            logger.warning(f"Failed to load modules config, using defaults: {e}")
    else:
        logger.debug(f"Modules config not found: {modules_config_path}")

    logger.info(f"Configuration loaded successfully from {config_dir}")

    return config
