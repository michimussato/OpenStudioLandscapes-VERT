import enum
import pathlib

from dagster import get_dagster_logger
from pydantic import (
    Field,
    HttpUrl,
    PositiveInt,
)

LOGGER = get_dagster_logger(__name__)

from OpenStudioLandscapes.engine.config.models import FeatureBaseModel

from OpenStudioLandscapes.VERT import dist

config_default = pathlib.Path(__file__).parent.joinpath("config_default.yml")
CONFIG_STR = config_default.read_text()


class Branches(enum.StrEnum):
    main = "main"


class Config(FeatureBaseModel):

    feature_name: str = dist.name

    definitions: str = "OpenStudioLandscapes.VERT.definitions"

    docker_compose_override: pathlib.Path = Field(
        default=pathlib.Path(
            "{DOT_LANDSCAPES}/{LANDSCAPE}/{FEATURE}/docker_compose/docker-compose.override.yml"
        ),
        description="The path to the `docker-compose.yml` file.",
    )
    vert_port_container: PositiveInt = Field(
        default=80,
        description="The VERT container port.",
        frozen=True,
    )
    vert_port_host: PositiveInt = Field(
        default=4546,
        description="The VERT host port.",
        frozen=False,
    )
    repository_url: HttpUrl = Field(
        default="https://github.com/VERT-sh/VERT.git",
    )
    repository_branch: Branches = Field(
        default=Branches.main,
        examples=[i.name for i in Branches],
    )
    repository_subdir: str = Field(
        default="VERT",
    )
    docker_compose_yml: str = Field(
        default="docker-compose.yml",
    )
    # docker_compose_worker_yml: str = Field(
    #     default="docker-compose.worker.yml",
    # )

    # EXPANDABLE PATHS
    @property
    def docker_compose_override_expanded(self) -> pathlib.Path:
        LOGGER.debug(f"{self.env = }")
        if self.env is None:
            raise KeyError("`env` is `None`.")
        LOGGER.debug(f"Expanding {self.docker_compose_override}...")
        ret = pathlib.Path(
            self.docker_compose_override.expanduser()
            .as_posix()
            .format(
                **{
                    "FEATURE": self.feature_name,
                    **self.env,
                }
            )
        )
        return ret
