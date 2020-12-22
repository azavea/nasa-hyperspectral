package azavea.nasa.hsi

import cats.effect.{ExitCode, IO}
import com.azavea.stac4s._
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff.GeoTiff
import io.circe._
import io.circe.syntax._
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.model.PutObjectRequest
import software.amazon.awssdk.core.sync.RequestBody

object Commands {

  def clipCog(clipCogConfig: ClipCogConfig): IO[ExitCode] = IO {
    print(s"${clipCogConfig.itemId} : ${clipCogConfig.collectionId}")
    val stacClient = StacClient(clipCogConfig.stacApiUrl)
    val item = stacClient.getStacItem(clipCogConfig.itemId.value)

    val cogAsset = item.assets
      .get(clipCogConfig.assetId.value)
      .orElse(throw new Exception(s"No STAC Asset for id: ${clipCogConfig.assetId.value}"))
      .get

    // Clip COG via RasterSource and upload to S3
    val rs = RasterSource(cogAsset.href)
    val geotiff = rs.read(clipCogConfig.extent) match {
      case Some(raster) => GeoTiff(raster, rs.crs)
      case None =>
        throw new Exception(
          s"Unable to read ${clipCogConfig.extent} from ${cogAsset.href}!"
        )
    }
    val resultId = s"${clipCogConfig.collectionId}-${clipCogConfig.itemId.value}"
    val cogData = geotiff.toCloudOptimizedByteArray
    val s3Client = S3Client.create
    val targetS3Key = s"activator-cog-clip/$resultId.tiff"
    val objectRequest = PutObjectRequest.builder
      .bucket(clipCogConfig.targetS3Bucket.value)
      .key(targetS3Key)
      .build
    s3Client.putObject(objectRequest, RequestBody.fromBytes(cogData))

    val cogAssetHref = s"s3://${clipCogConfig.targetS3Bucket.value}/$targetS3Key"
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

    if (stacClient.getStacCollection(CogClipCollection.id).isEmpty) {
      stacClient.postStacCollection(CogClipCollection)
    }

    stacClient.postStacCollectionItem(CogClipCollection.id, cogItem)
    ExitCode.Success
  }
}
