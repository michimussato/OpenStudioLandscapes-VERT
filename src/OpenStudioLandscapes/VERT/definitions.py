from dagster import (
    Definitions,
    load_assets_from_modules,
)

import OpenStudioLandscapes.VERT.assets

assets = load_assets_from_modules(
    modules=[OpenStudioLandscapes.VERT.assets],
)


defs = Definitions(
    assets=[
        *assets,
    ],
)
