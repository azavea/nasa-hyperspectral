package azavea.nasa.hsi

import cats.implicits._
import com.azavea.stac4s._
import com.monovore.decline._
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.raster.io.geotiff.MultibandGeoTiff
import geotrellis.vector.Extent
import io.circe._
import io.circe.syntax._
import io.lemonlabs.uri.Url
import software.amazon.awssdk.services.s3.S3Client
import software.amazon.awssdk.services.s3.model.PutObjectRequest
import software.amazon.awssdk.core.sync.RequestBody

import java.util.UUID

/**
  * TODO:
  * - [ ] Refactor to use FeatureCollection of geoms to clip multiple items
  * - [ ] Refactor to use s"$sourceCollection-$sourceFeatureId" as Clipped COG STAC Item ID
  * - [ ] Refactor to use github.com/azavea/azavea.g8 Commands template:
  *       https://github.com/azavea/azavea.g8/blob/master/src/main/g8/application/src/main/scala/%24package__packaged%24/api/commands/Commands.scala
  * - [ ] https://github.com/azavea/nasa-hyperspectral/issues/80 and then use here
  */
object CogClip
    extends CommandApp(
      name = "cog-clip",
      header =
        "Clip COG in STAC Item to extent. Publish result and create STAC Item in provided Collection.",
      main = {

        val stacApiUrlEnvVar = "STAC_API_URL"
        val stacApiUrlHelp =
          s"Url to root of STAC API to interface with. Defaults to $stacApiUrlEnvVar."

        val resultIdOpt = Opts.argument[UUID]("result-uuid")
        val itemIdOpt = Opts.argument[String]("stac-item-id")
        val assetIdOpt = Opts.argument[String]("stac-asset-id")
        val extentOpt = Opts.argument[Extent]("extent")
        val targetBucketOpt =
          Opts.option[String]("target-bucket", help = "", metavar = "")
        val targetCollectionOpt = Opts.argument[String]("target-collection")
        val stacApiUrlOpt =
          Opts.option[Url]("stac-api-url", help = stacApiUrlHelp) orElse
            Opts.env[Url](
              stacApiUrlEnvVar,
              help = stacApiUrlHelp,
              metavar = "url"
            )

        (
          resultIdOpt,
          itemIdOpt,
          assetIdOpt,
          extentOpt,
          stacApiUrlOpt,
          targetBucketOpt
        ).mapN {
          (resultId, itemId, assetId, extent, stacApiUrl, targetBucket) =>
            println(s"Hello $itemId.$assetId: $extent!")

            val stacClient = StacClient(stacApiUrl)
            val item = stacClient.getStacItem(itemId)

            val cogAsset = item.assets
              .get(assetId)
              .orElse(throw new Exception(s"No STAC Asset for id: $assetId"))
              .get

            // Clip COG via RasterSource and upload to S3
            val rs = RasterSource(cogAsset.href)
            val geotiff: MultibandGeoTiff = rs.read(extent) match {
              case Some(raster) => GeoTiff(raster, rs.crs)
              case None =>
                throw new Exception(
                  s"Unable to read $extent from ${cogAsset.href}!"
                )
            }
            val cogData = geotiff.toCloudOptimizedByteArray
            val s3Client = S3Client.create
            val targetKey = s"activator-cog-clip/$resultId.tiff"
            val objectRequest = PutObjectRequest.builder
              .bucket(targetBucket)
              .key(targetKey)
              .build
            s3Client.putObject(objectRequest, RequestBody.fromBytes(cogData))

            val cogAssetHref = s"s3://$targetBucket/$targetKey"
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
              "sourceAssetId" -> assetId
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
        }
      }
    )
