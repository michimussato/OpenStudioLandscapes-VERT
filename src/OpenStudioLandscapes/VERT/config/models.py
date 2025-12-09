import pathlib
import textwrap

from pydantic import (
    Field,
    PositiveInt, HttpUrl,
)

from OpenStudioLandscapes.engine.config.models import FeatureBaseModel
from OpenStudioLandscapes.VERT.config import dist


CONFIG_STR = textwrap.dedent(
    """
    # Base Information
    group_name: "VERT"
    key_prefixes:
      - "VERT"
    
    vert_port_container: 80
    vert_port_host: 3344
    """
)


class Config(FeatureBaseModel):
    feature_name: str = dist.name
    compose_scope: str = "default"
    definitions: str = "OpenStudioLandscapes.VERT.definitions"

    docker_compose_override: pathlib.Path = Field(
        default="{DOT_LANDSCAPES}/{LANDSCAPE}/{FEATURE}/docker_compose/docker-compose.override.yml",
        description="The path to the `docker-compose.yml` file.",
    )
    vert_port_container: PositiveInt = Field(
        default=80,
        description="The VERT container port.",
        frozen=True,
    )
    vert_port_host: PositiveInt = Field(
        default=4545,
        description="The VERT host port.",
        frozen=False,
    )
    repository_url: HttpUrl = Field(
        default="https://github.com/VERT-sh/VERT.git",
    )
    repository_branch: str = Field(
        default="main",
    )
    repository_subdir: str = Field(
        default="VERT",
    )
    docker_compose_yml: str = Field(
        default="docker-compose.yml",
    )
    docker_compose_worker_yml: str = Field(
        default="docker-compose.worker.yml",
    )
