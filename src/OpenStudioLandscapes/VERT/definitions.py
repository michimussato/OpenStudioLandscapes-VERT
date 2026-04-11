from dagster import (
    Definitions,
    load_assets_from_modules,
)

import OpenStudioLandscapes.VERT.assets

assets_base = load_assets_from_modules(
    modules=[OpenStudioLandscapes.VERT.assets],
)


defs = Definitions(
    assets=[
        *assets_base,
    ],
)
