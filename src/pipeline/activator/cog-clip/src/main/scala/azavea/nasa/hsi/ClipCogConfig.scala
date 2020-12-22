package azavea.nasa.hsi

import eu.timepit.refined.types.string.NonEmptyString
import io.lemonlabs.uri.Url
import geotrellis.vector.Extent

case class ClipCogConfig(
    assetId: NonEmptyString,
    collectionId: NonEmptyString,
    extent: Extent,
    itemId: NonEmptyString,
    stacApiUrl: Url,
    targetS3Bucket: NonEmptyString,
)
