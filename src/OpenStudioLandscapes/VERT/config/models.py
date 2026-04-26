import enum
import pathlib
from typing import List

from dagster import get_dagster_logger
from pydantic import (
    Field,
    HttpUrl,
    PositiveInt,
    computed_field,
)

LOGGER = get_dagster_logger(__name__)

from OpenStudioLandscapes.engine.config.models import FeatureBaseModel

from OpenStudioLandscapes.VERT import constants, dist


class Branches(enum.StrEnum):
    main = "main"


class Config(FeatureBaseModel):

    feature_name: str = dist.name

    group_name: str = constants.ASSET_HEADER["group_name"]

    key_prefixes: List[str] = constants.ASSET_HEADER["key_prefix"]

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
    @computed_field
    @property
    def docker_compose_override_expanded(self) -> pathlib.Path:
        LOGGER.debug(f"{self.env = }")
        if self.env is None:
            raise KeyError("`env` is `None`.")
        LOGGER.debug(f"Expanding {self.docker_compose_override}...")
        ret = pathlib.Path(
            self.docker_compose_override.expanduser()  # pylint: disable=E1101
            .as_posix()
            .format(
                **{
                    "FEATURE": self.feature_name,
                    **self.env,
                }
            )
        )
        return ret


CONFIG_STR = Config.get_docs()
