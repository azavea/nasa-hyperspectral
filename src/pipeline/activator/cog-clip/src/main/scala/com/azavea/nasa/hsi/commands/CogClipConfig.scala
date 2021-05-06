package com.azavea.nasa.hsi.commands

import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector.{io => _}
import geotrellis.vector.io.json.JsonFeatureCollection
import io.circe.generic.JsonCodec
import io.circe.refined._
import eu.timepit.refined.types.all.PosInt
import eu.timepit.refined.types.string.NonEmptyString

import java.net.URI

@JsonCodec
case class CogClipConfig(
  sourceCollectionId: NonEmptyString,
  sourceItemId: NonEmptyString,
  sourceAssetId: NonEmptyString,
  targetCollectionId: NonEmptyString,
  targetLayerId: Option[NonEmptyString],
  features: JsonFeatureCollection,
  stacApiURI: URI,
  targetS3URI: AmazonS3URI,
  threads: PosInt,
  withGDAL: Boolean,
  force: Boolean
) {
  def resultId(featureId: NonEmptyString): NonEmptyString =
    NonEmptyString.unsafeFrom(s"$sourceCollectionId-$targetCollectionId-$sourceItemId-$featureId")
  def cogAssetHref(featureId: NonEmptyString): NonEmptyString =
    NonEmptyString.unsafeFrom(s"$targetS3URI${resultId(featureId)}.tiff")
  def cogAssetHrefLocal(featureId: NonEmptyString): NonEmptyString =
    NonEmptyString.unsafeFrom(s"/tmp/${resultId(featureId)}.tiff")
  def cogAssetHrefPath(featureId: NonEmptyString): AmazonS3URI =
    new AmazonS3URI(cogAssetHref(featureId).value)
}
