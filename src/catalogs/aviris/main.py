from datetime import datetime, timezone

import pystac
import stacframes

from aviris_df import AvirisClassic, AvirisNg, AVIRIS_DESCRIPTION


def main():
    df = AvirisClassic.as_df("aviris-flight-lines.csv")
    collection = pystac.Collection(
        AvirisClassic.COLLECTION_NAME,
        AVIRIS_DESCRIPTION,
        pystac.Extent(
            spatial=pystac.SpatialExtent([[None, None, None, None]]),
            temporal=pystac.TemporalExtent(
                [[datetime(1970, 1, 1, tzinfo=timezone.utc), None]]
            ),
        ),
    )
    stacframes.df_to(collection, df)

    df_ng = AvirisNg.as_df("aviris-ng-flight-lines.csv")
    collection_ng = pystac.Collection(
        AvirisNg.COLLECTION_NAME,
        AVIRIS_DESCRIPTION,
        pystac.Extent(
            spatial=pystac.SpatialExtent([[None, None, None, None]]),
            temporal=pystac.TemporalExtent(
                [[datetime(1970, 1, 1, tzinfo=timezone.utc), None]]
            ),
        ),
    )
    stacframes.df_to(collection_ng, df_ng)

    # Normalize before validation to set all the required object links
    catalog = pystac.Catalog("aviris", AVIRIS_DESCRIPTION)
    catalog.add_child(collection)
    catalog.add_child(collection_ng)
    catalog_path = "./data/catalog"
    catalog.normalize_hrefs(catalog_path)
    print("Validating catalog...")
    catalog.validate_all()
    print("Saving catalog to {}...".format(catalog_path))
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print("Done!")


if __name__ == "__main__":
    main()
