package com.azavea.nasa.hsi.commands

import eu.timepit.refined.types.all.PosInt
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector.io.json.JsonFeatureCollection

import java.net.URI

case class CogClipConfig(
  assetId: NonEmptyString,
  collectionId: NonEmptyString,
  itemId: NonEmptyString,
  features: JsonFeatureCollection,
  stacApiURI: URI,
  targetS3URI: AmazonS3URI,
  threads: PosInt
) {
  lazy val resultId     = s"$collectionId-$itemId"
  lazy val cogAssetHref = s"$targetS3URI$resultId.tiff"
}
