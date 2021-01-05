package azavea.nasa.hsi

import eu.timepit.refined.types.string.NonEmptyString
import io.lemonlabs.uri.Url
import geotrellis.vector.io.json.JsonFeatureCollection

case class ClipCogConfig(
  assetId: NonEmptyString,
  collectionId: NonEmptyString,
  features: JsonFeatureCollection,
  itemId: NonEmptyString,
  stacApiUrl: Url,
  targetS3Bucket: NonEmptyString
)
