package azavea.nasa.hsi

import cats.data.Validated
import cats.implicits._
import com.monovore.decline._
import com.monovore.decline.refined._
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.vector.Extent
import geotrellis.vector.io.json._
import io.lemonlabs.uri.Url
import io.circe.Json

import java.util.UUID
import scala.util.{Failure, Success, Try}

trait ClipCogOptions {

  private val assetId = Opts.argument[NonEmptyString]("stac-asset-id")

  private val collectionId = Opts.argument[NonEmptyString]("collection-id")

  private val features = Opts.option[JsonFeatureCollection](
    "features",
    help = "Feature Collection of features to clip from COG"
  ) orElse Opts
    .env[JsonFeatureCollection](
      "ACC_FEATURES",
      help = "Feature Collection of features to clip from COG"
    )
    .withDefault(JsonFeatureCollection(List.empty[Json]))

  private val itemId = Opts.argument[NonEmptyString]("stac-item-id")

  private val stacApiUrlHelp = ""
  private val stacApiUrl     = (Opts
    .option[Url](
      "stac-api-url",
      help = stacApiUrlHelp
    )
    orElse
    Opts
      .env[Url](
        "STAC_API_URL",
        help = stacApiUrlHelp
      )
      .withDefault(Url.parse("http://localhost:9090")))

  private val targetS3Bucket = (Opts
    .option[NonEmptyString]("target-s3-bucket", help = "")
    orElse
    Opts
      .env[NonEmptyString]("ACC_TARGET_S3_BUCKET", help = "")
      .withDefault(NonEmptyString("nasa-hsi-activator-clip-cogs")))

  val clipCogConfig: Opts[ClipCogConfig] =
    (
      assetId,
      collectionId,
      features,
      itemId,
      stacApiUrl,
      targetS3Bucket
    ) mapN ClipCogConfig
}
