from dagster import (
    Definitions,
    load_assets_from_modules,
)

import OpenStudioLandscapes.VERT.assets
import OpenStudioLandscapes.VERT.constants

assets = load_assets_from_modules(
    modules=[OpenStudioLandscapes.VERT.assets],
)

constants = load_assets_from_modules(
    modules=[OpenStudioLandscapes.VERT.constants],
)


defs = Definitions(
    assets=[
        *assets,
        *constants,
    ],
)
