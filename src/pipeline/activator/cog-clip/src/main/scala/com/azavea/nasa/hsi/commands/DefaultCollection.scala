package com.azavea.nasa.hsi.commands

import com.azavea.stac4s._

import cats.syntax.option._
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.vector.{io => _, _}
import io.circe.JsonObject
import io.circe.syntax._
import io.circe.refined._
import cats.syntax.functor._
import eu.timepit.refined.refineMV

import java.time.{LocalDate, ZoneOffset}

object DefaultCollection {
  def collection(id: String): StacCollection = StacCollection(
    _type = refineMV("Collection"),
    stacVersion = "1.0.0",
    stacExtensions = Nil,
    id = id,
    title = "".some,
    description = "A STAC Collection containing COGs created by the nasa-hsi cog-clip activator",
    keywords = Nil,
    license = Proprietary(),
    providers = Nil,
    extent = StacExtent(
      SpatialExtent(
        List(
          TwoDimBbox(
            -180,
            -90,
            180,
            90
          )
        )
      ),
      Interval(
        List(
          TemporalExtent(
            LocalDate.of(2006, 1, 1).atStartOfDay().toInstant(ZoneOffset.UTC),
            LocalDate.of(2020, 1, 1).atStartOfDay().toInstant(ZoneOffset.UTC)
          )
        )
      )
    ),
    summaries = Map.empty,
    properties = JsonObject.empty,
    links = Nil,
    extensionFields = JsonObject.empty,
    assets = None
  )

  def item(clipConfig: CogClipConfig, featureId: NonEmptyString, sourceItem: StacItem, geometry: Geometry): StacItem = {
    val defaultTargetCollection = collection(clipConfig.targetCollectionId.value)
    val layerIds                = clipConfig.targetLayerId.getOrElse(clipConfig.targetCollectionId) :: Nil
    StacItem(
      id = clipConfig.resultId(featureId).value,
      stacVersion = defaultTargetCollection.stacVersion,
      stacExtensions = layerIds.as("layer"),
      _type = "Feature",
      geometry = geometry,
      bbox = geometry.extent.toTwoDimBbox,
      links = Nil,
      assets = Map(
        clipConfig.sourceAssetId.value -> StacAsset(
          href = clipConfig.cogAssetHref(featureId).value,
          title = clipConfig.sourceAssetId.value.some,
          description = None,
          roles = Set(StacAssetRole.Data),
          _type = `image/cog`.some
        )
      ),
      collection = defaultTargetCollection.id.some,
      properties = LensItemPropertiesExtensionFields.set(
        JsonObject(
          "layer:ids"        -> layerIds.asJson,
          "sourceCollection" -> clipConfig.sourceCollectionId.asJson,
          "sourceItemId"     -> sourceItem.id.asJson,
          "sourceAssetId"    -> clipConfig.sourceAssetId.asJson
        )
      )(sourceItem.properties)
    )
  }
}
