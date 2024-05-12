from pathlib import Path
from typing import Optional, Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

DEFAULT_CONFIG_PATH = Path.home() / ".surf-archiver" / "config.yaml"


class Config(BaseSettings):

    target_dir: Path = Path.home() / "prince"
    connection_url: str = "amqp://guest:guest@localhost"
    bucket: str = "prince-archiver-dev"
    log_file: Optional[Path] = Path.home() / ".surf-archiver" / "app.log"

    model_config = SettingsConfigDict(env_prefix="SURF_ARCHIVER")


def get_config(config_path: Path) -> Config:
    class _Config(Config):

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> Tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                env_settings,
                YamlConfigSettingsSource(settings_cls, yaml_file=config_path),
            )

    return _Config()
