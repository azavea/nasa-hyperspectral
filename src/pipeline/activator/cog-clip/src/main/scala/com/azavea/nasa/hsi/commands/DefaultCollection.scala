package com.azavea.nasa.hsi.commands

import com.azavea.stac4s._
import com.azavea.stac4s.types.TemporalExtent
import cats.syntax.option._
import geotrellis.raster.io.geotiff.MultibandGeoTiff
import io.circe.JsonObject
import io.circe.syntax._

import java.time.{LocalDate, ZoneOffset}

object DefaultCollection {
  val Collection: StacCollection = StacCollection(
    stacVersion = "1.0.0-beta.2",
    stacExtensions = Nil,
    id = "nasa-hsi-activator-cog-clip",
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
    summaries = JsonObject.empty,
    properties = JsonObject.empty,
    links = Nil,
    extensionFields = JsonObject.empty
  )

  def from(clipConfig: CogClipConfig, sourceItemId: String, geotiff: MultibandGeoTiff): StacItem =
    StacItem(
      id = clipConfig.resultId,
      stacVersion = DefaultCollection.stacVersion,
      stacExtensions = Nil,
      _type = "Feature",
      geometry = geotiff.extent.toPolygon,
      bbox = geotiff.extent.toTwoDimBbox,
      links = Nil,
      assets = Map(
        "cog" -> StacItemAsset(
          href = clipConfig.cogAssetHref,
          title = "cog".some,
          description = None,
          roles = Set(StacAssetRole.Data),
          _type = `image/cog`.some
        )
      ),
      collection = DefaultCollection.id.some,
      properties = Map(
        "collection"    -> DefaultCollection.id,
        "sourceItemId"  -> sourceItemId,
        "sourceAssetId" -> clipConfig.assetId.value
      ).asJsonObject
    )

  implicit def objectToInstance(obj: DefaultCollection.type): StacCollection = Collection
}
