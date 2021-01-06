package com.azavea.nasa.hsi.commands

import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.vector.io.json.JsonFeatureCollection
import io.lemonlabs.uri.Url

case class CogClipConfig(
  assetId: NonEmptyString,
  collectionId: NonEmptyString,
  features: JsonFeatureCollection,
  itemId: NonEmptyString,
  stacApiUrl: Url,
  targetS3Bucket: NonEmptyString
) {
  lazy val resultId = s"$collectionId-$itemId"
  // should be configurable?
  lazy val targetS3Key  = s"activator-cog-clip/$resultId.tiff"
  lazy val cogAssetHref = s"s3://$targetS3Bucket/$targetS3Key"
}
