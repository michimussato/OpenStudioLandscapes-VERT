import copy
import textwrap
import json
import pathlib
from collections import ChainMap
from functools import reduce
from typing import Any, Generator, List, MutableMapping

from deepdiff import DeepDiff
from pydantic_core._pydantic_core import ValidationError

import git
import yaml
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetMaterialization,
    MetadataValue,
    Output,
    asset,
)
from docker_compose_graph.utils import *
from docker_compose_graph.yaml_tags.overrides import *
from git.exc import GitCommandError
from OpenStudioLandscapes.engine.common_assets.docker_compose_graph import (
    get_docker_compose_graph,
)
from OpenStudioLandscapes.engine.common_assets.feature_out import get_feature_out
from OpenStudioLandscapes.engine.common_assets.group_in import get_group_in
from OpenStudioLandscapes.engine.common_assets.group_out import get_group_out
from OpenStudioLandscapes.engine.config.models import ConfigEngine, DockerConfigModel
import OpenStudioLandscapes.engine.discovery.discovery as discovery
from OpenStudioLandscapes.engine.constants import *
from OpenStudioLandscapes.engine.enums import *
from OpenStudioLandscapes.engine.utils import *
from OpenStudioLandscapes.engine.utils.docker.compose_dicts import *
from OpenStudioLandscapes.engine.discovery.get_feature_base_model import get_feature_base_model

from OpenStudioLandscapes.VERT.constants import *
from OpenStudioLandscapes.VERT.config.models import Config, CONFIG_STR

from OpenStudioLandscapes.VERT.config import dist

group_in = get_group_in(
    ASSET_HEADER=ASSET_HEADER,
    ASSET_HEADER_PARENT=ASSET_HEADER_BASE,
    input_name=str(GroupIn.BASE_IN),
)

group_out = get_group_out(
    ASSET_HEADER=ASSET_HEADER,
)

docker_compose_graph = get_docker_compose_graph(
    ASSET_HEADER=ASSET_HEADER,
)

feature_out = get_feature_out(
    ASSET_HEADER=ASSET_HEADER,
    feature_out_ins={
        "compose": dict,
        "group_in": dict,
        "CONFIG": Config,
    },
)


# @asset(
#     **ASSET_HEADER,
#     deps=[
#         # This dep is needed for this Asset
#         # to be evaluated AFTER
#         # upstream Features (Asset Groups)
#         AssetKey([*ASSET_HEADER["key_prefix"], "group_in"]),
#     ],
#     description=textwrap.dedent(
#         """
#         Loads the default `config.yml` that comes with
#         the Feature itself. Contents are being validated
#         against a `pydantic.BaseModel` in this step.
#         """
#     )
# )
# def CONFIG_BLUEPRINT(
#     context: AssetExecutionContext,
# ) -> Generator[
#     Output[str] | AssetMaterialization,
#     None,
#     None,
# ]:
#
#     with open(pathlib.Path(__file__).parent / "config" / "config_blueprint.yml") as fr:
#         # This is str so that comments are read as well
#         config_str: str = fr.read()
#
#     config = yaml.safe_load(config_str)
#
#     try:
#         context.log.info(f"Validating: {config = }")
#         _config_validated = Config(**config)
#         context.log.debug(f"Validated.")
#     except ValidationError as err:
#         context.log.error(
#             "Config Validation failed. "
#             "The default `config.yml` for "
#             f"{dist.name} contains "
#             "errors, missing and/or illegal parameters."
#         )
#         raise ValidationError from err
#
#     yield Output(config_str)
#
#     diff = DeepDiff(
#         config,
#         # We don't want to compare expanded
#         # with non-expanded dicts - creates too
#         # much noise in the diff
#         _config_validated.model_dump(mode="json")
#     )
#
#     yield AssetMaterialization(
#         asset_key=context.asset_key,
#         metadata={
#             "__".join(context.asset_key.path): MetadataValue.md(f"```yaml\n{config_str}\n```"),
#             "diff": MetadataValue.md(f"```json\n{json.dumps(diff, indent=2, default=str)}\n```"),
#         },
#     )


@asset(
    **ASSET_HEADER,
    ins={
        "group_in": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "group_in"]),
        ),
    },
    description=textwrap.dedent(
        f"""
Reads options from a custom `config.yml`.
If the custom `config.yml` does not exist, it 
will be created locally containing default options.

---

For reference, the default `config.yml` looks as follows:
        
```yaml
{CONFIG_STR}
```
"""
    )
)
def CONFIG(
    context: AssetExecutionContext,
    group_in: dict,  # pylint: disable=redefined-outer-name
) -> Generator[
    Output[discovery.FeatureBaseModel]
    | AssetMaterialization,
    None,
    None,
]:

    env: dict = group_in.pop("env")

    config_validated: discovery.FeatureBaseModel = get_feature_base_model(
        context=context,
        discovered_models=discovery.DISCOVERED_MODELS,
        distribution=dist,
    )
    config_validated.env = env

    yield Output(config_validated)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.md(
                f"```json\n{config_validated.model_dump_json(fallback=str, indent=2)}\n```"
            ),
        },
    )


@asset(
    **ASSET_HEADER,
    ins={
        "CONFIG": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "CONFIG"]),
        ),
    },
)
def compose_networks(
    context: AssetExecutionContext,
    CONFIG: Config,
) -> Generator[
    Output[dict[str, dict[str, dict[str, str]]]] | AssetMaterialization, None, None
]:

    env: dict = CONFIG.env

    compose_network_mode = DockerComposePolicies.NETWORK_MODE.BRIDGE

    docker_dict = get_network_dicts(
        context=context,
        compose_network_mode=compose_network_mode,
        env=env,
    )

    docker_yaml = yaml.dump(docker_dict)

    yield Output(docker_dict)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.json(docker_dict),
            "compose_network_mode": MetadataValue.text(compose_network_mode.value),
            "docker_yaml": MetadataValue.md(f"```shell\n{docker_yaml}\n```"),
        },
    )


@asset(
    **ASSET_HEADER,
    ins={},
)
def cmd_extend(
    context: AssetExecutionContext,
) -> Generator[Output[list[Any]] | AssetMaterialization | Any, Any, None]:

    ret = []

    yield Output(ret)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.json(ret),
        },
    )


@asset(
    **ASSET_HEADER,
    ins={},
)
def cmd_append(
    context: AssetExecutionContext,
) -> Generator[Output[dict[str, list[Any]]] | AssetMaterialization | Any, Any, None]:

    ret = {"cmd": [], "exclude_from_quote": []}

    yield Output(ret)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.json(ret),
        },
    )


@asset(
    **ASSET_HEADER,
    ins={
        "CONFIG": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "CONFIG"]),
        ),
    },
)
def clone_repository(
    context: AssetExecutionContext,
    CONFIG: Config,
) -> Generator[Output[pathlib.Path] | AssetMaterialization, None, None]:

    env: dict = CONFIG.env

    repo_dir = pathlib.Path(
        env["DOT_LANDSCAPES"],
        env.get("LANDSCAPE", "default"),
        f"{dist.name}",
        "__".join(context.asset_key.path),
        "repos",
    )

    repository_dir_full = repo_dir / CONFIG.repository_subdir
    repository_dir_full.parent.mkdir(parents=True, exist_ok=True)

    try:
        git.Repo.clone_from(
            url=CONFIG.repository_url,
            to_path=repository_dir_full,
            branch=CONFIG.repository_branch,
        )
    except GitCommandError as e:
        context.log.warning("Pulling from Repo (%s)" % e)
        existing_repo = git.Repo(repository_dir_full)
        origin = existing_repo.remotes.origin
        origin.pull()

    yield Output(repository_dir_full)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.path(repository_dir_full),
        },
    )


# Todo:
#  - [ ] Maybe fix this Non-Standard `compose` implementation
@asset(
    **ASSET_HEADER,
    ins={
        "compose_networks": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "compose_networks"]),
        ),
        "clone_repository": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "clone_repository"]),
        ),
        "CONFIG": AssetIn(
            AssetKey([*ASSET_HEADER["key_prefix"], "CONFIG"]),
        ),
    },
)
def compose(
    context: AssetExecutionContext,
    compose_networks: dict,  # pylint: disable=redefined-outer-name
    clone_repository: pathlib.Path,  # pylint: disable=redefined-outer-name
    CONFIG: Config,  # pylint: disable=redefined-outer-name
) -> Generator[
    Output[MutableMapping[str, List[MutableMapping[str, List[str]]]]]
    | AssetMaterialization,
    None,
    None,
]:
    """"""

    env: dict = CONFIG.env

    config_engine: ConfigEngine = CONFIG.config_engine

    docker_compose_override: pathlib.Path = CONFIG.docker_compose_override_expanded
    context.log.debug(f"{docker_compose_override = }")
    docker_compose_override.parent.mkdir(parents=True, exist_ok=True)

    network_dict = {}
    ports_dict = {}

    if "networks" in compose_networks:
        network_dict = {"networks": list(compose_networks.get("networks", {}).keys())}
        ports_dict = {
            "ports": OverrideArray(
                [
                    f"{CONFIG.vert_port_host}:{CONFIG.vert_port_container}",
                ]
            ),
        }
    elif "network_mode" in compose_networks:
        network_dict = {"network_mode": compose_networks.get("network_mode")}

    parent = clone_repository / CONFIG.docker_compose_yml

    volumes_dict = {"volumes": []}

    # For portability, convert absolute volume paths to relative paths

    _volume_relative = []

    for v in volumes_dict["volumes"]:

        host, container = v.split(":", maxsplit=1)

        volume_dir_host_rel_path = get_relative_path_via_common_root(
            context=context,
            # path_src=pathlib.Path(env["DOCKER_COMPOSE"]),
            # This leads to a wrong relative path (missing one "parent")
            # path element.
            # It uses {DOT_LANDSCAPES}/{LANDSCAPE}/Ayon__Ayon/Ayon__DOCKER_COMPOSE/docker_compose/docker-compose.yml
            # as the starting point but does not lead to the correct resolution.
            # In fact, it seems like the actual CWD for this is the docker-compose.yml
            # from the repo (main entry point) which seems to lead to an incorrect amount
            # of `cd ..` actions.
            # Let's try with the yml from the repo as the path_src instead of the one from
            # "DOCKER_COMPOSE"
            # => seems to do the trick to make sure, we end up using the directory
            # we intended to use
            path_src=CONFIG.docker_compose_expanded,
            path_dst=pathlib.Path(host),
            path_common_root=pathlib.Path(env["DOT_LANDSCAPES"]),
        )

        _volume_relative.append(
            f"{volume_dir_host_rel_path.as_posix()}:{container}",
        )

    volumes_dict = {
        "volumes": [
            # "/etc/localtime:/etc/localtime:ro",
            # *_volume_relative,
        ]
    }

    service_name = "vert"
    container_name, host_name = get_docker_compose_names(
        context=context,
        service_name=service_name,
        landscape_id=env.get("LANDSCAPE", "default"),
        domain_lan=config_engine.openstudiolandscapes__domain_lan,
    )
    # container_name = "--".join([f"{service_name}", env.get("LANDSCAPE", "default")])
    # host_name = ".".join([env["HOSTNAME"], env["OPENSTUDIOLANDSCAPES__DOMAIN_LAN"]])

    docker_dict_override = {
        "services": {
            service_name: {
                "container_name": container_name,
                "hostname": host_name,
                "domainname": config_engine.openstudiolandscapes__domain_lan,
                **copy.deepcopy(ports_dict),
                **copy.deepcopy(volumes_dict),
                **copy.deepcopy(network_dict),
            },
        },
    }

    if "networks" in compose_networks:
        network_dict = copy.deepcopy(compose_networks)
    else:
        network_dict = {}

    docker_chainmap = ChainMap(
        network_dict,
        docker_dict_override,
    )

    docker_dict = reduce(deep_merge, docker_chainmap.maps)

    docker_yaml_override: str = yaml.dump(docker_dict)

    with open(docker_compose_override, "w") as fw:
        fw.write(docker_yaml_override)

    # Write compose override to disk here to be able to reference
    # it in the following step.
    # It seems that it's necessary to apply overrides in
    # include: path

    # Convert absolute paths in `include` to
    # relative ones
    DOCKER_COMPOSE = CONFIG.docker_compose_expanded
    DOCKER_COMPOSE.parent.mkdir(parents=True, exist_ok=True)

    rel_paths = []
    dot_landscapes = pathlib.Path(env["DOT_LANDSCAPES"])

    for path in [
        parent,
        CONFIG.docker_compose_override_expanded,
    ]:

        context.log.debug(f"{path = }")
        rel_path = get_relative_path_via_common_root(
            context=context,
            path_src=CONFIG.docker_compose_expanded,
            path_dst=path,
            path_common_root=dot_landscapes,
        )

        rel_paths.append(rel_path.as_posix())

    docker_dict_include = {
        "include": [
            {
                "path": rel_paths,
            },
        ],
    }

    docker_yaml_include = yaml.dump(docker_dict_include)

    # Write docker-compose.yaml
    with open(DOCKER_COMPOSE, mode="w", encoding="utf-8") as fw:
        fw.write(docker_yaml_include)

    yield Output(docker_dict_include)

    yield AssetMaterialization(
        asset_key=context.asset_key,
        metadata={
            "__".join(context.asset_key.path): MetadataValue.json(docker_dict_include),
            "docker_yaml_override": MetadataValue.md(
                f"```yaml\n{docker_yaml_override}\n```"
            ),
            "path_docker_yaml_override": MetadataValue.path(DOCKER_COMPOSE),
        },
    )
