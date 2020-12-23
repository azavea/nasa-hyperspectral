package azavea.nasa.hsi

import cats.effect.{ExitCode, IO}
import com.azavea.stac4s._
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.vector._
import geotrellis.vector.io.json._
import _root_.io.circe._
import _root_.io.circe.syntax._

object Commands {

  def clipCog(clipCogConfig: ClipCogConfig): IO[ExitCode] = IO {
    print(s"${clipCogConfig.itemId} : ${clipCogConfig.collectionId}")
    val stacClient = StacClient(clipCogConfig.stacApiUrl)
    val item = stacClient.getStacItem(clipCogConfig.itemId.value)

    val cogAsset = item.assets
      .get(clipCogConfig.assetId.value)
      .orElse(throw new Exception(s"No STAC Asset for id: ${clipCogConfig.assetId.value}"))
      .get

    if (stacClient.getStacCollection(CogClipCollection.id).isEmpty) {
      stacClient.postStacCollection(CogClipCollection)
    }

    val rs = RasterSource(cogAsset.href)

    clipCogConfig.features.getAllFeatures[Feature[Geometry, Json]].foreach(feature => {
      val extent = feature.geom.extent
      val geotiff = rs.read(extent) match {
        case Some(raster) => GeoTiff(raster, rs.crs)
        case None =>
          throw new Exception(
            s"Unable to read ${extent} from ${cogAsset.href}!"
          )
      }
      val resultId = s"${clipCogConfig.collectionId}-${clipCogConfig.itemId.value}"
      val targetS3Key = s"activator-cog-clip/$resultId.tiff"
      val cogAssetHref = s"s3://${clipCogConfig.targetS3Bucket.value}/$targetS3Key"
      geotiff.write(cogAssetHref, optimizedOrder = true)

      val assets = Map(
        "cog" -> StacItemAsset(
          cogAssetHref,
          Some("cog"),
          None,
          Set(StacAssetRole.Data),
          Some(`image/cog`)
        )
      )
      val properties: JsonObject = Map(
        "collection" -> CogClipCollection.id,
        "sourceItemId" -> item.id,
        "sourceAssetId" -> clipCogConfig.assetId.value
      ).asJsonObject
      val cogItem = StacItem(
        resultId.toString,
        HsiStacVersion,
        List.empty[String],
        "Feature",
        geotiff.extent.toPolygon,
        geotiff.extent,
        List.empty[StacLink],
        assets,
        Some(CogClipCollection.id),
        properties
      )

      stacClient.postStacCollectionItem(CogClipCollection.id, cogItem)
      println(s"POST ${cogItem.id} to ${clipCogConfig.stacApiUrl}")
    })
    ExitCode.Success
  }
}
