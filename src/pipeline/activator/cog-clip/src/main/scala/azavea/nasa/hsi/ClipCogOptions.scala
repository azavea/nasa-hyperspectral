package azavea.nasa.hsi

import cats.data.Validated
import cats.implicits._
import com.monovore.decline._
import com.monovore.decline.refined._
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.vector.Extent
import io.lemonlabs.uri.Url

import java.util.UUID
import scala.util.{Failure, Success, Try}

trait ClipCogOptions {

  val clipCogConfig: Opts[ClipCogConfig] =
    (
      assetId,
      collectionId,
      extent,
      itemId,
      stacApiUrl,
      targetS3Bucket
    ) mapN ClipCogConfig

  private val assetId = Opts.argument[NonEmptyString]("stac-asset-id")

  private val collectionId = Opts.argument[NonEmptyString]("collection-id")

  private val extent = Opts.argument[Extent]("extent")

  private val itemId = Opts.argument[NonEmptyString]("stac-item-id")

  private val stacApiUrlHelp = ""
  private val stacApiUrl = (Opts
    .option[Url](
      "stac-api-url",
      help = stacApiUrlHelp,
      metavar = "stac-api-url"
    )
    orElse
      Opts
        .env[Url](
          "STAC_API_URL",
          help = stacApiUrlHelp,
          metavar = "stac-api-url"
        )
        .withDefault(Url.parse("http://localhost:9090")))

  private val targetS3Bucket = (Opts
    .option[NonEmptyString]("target-s3-bucket", help = "", metavar = "")
    orElse
      Opts
        .env[NonEmptyString]("ACC_TARGET_S3_BUCKET", help = "", metavar = "")
        .withDefault(NonEmptyString("nasa-hsi-activator-clip-cogs")))

  private implicit val extentArgument: Argument[Extent] = new Argument[Extent] {
    def read(string: String) = {
      string
        .replaceAll("\"", "")
        .replaceAll("'", "")
        .split(",")
        .map(x => Try(x.toDouble)) match {
        case Array(
              Success(minlon),
              Success(minlat),
              Success(maxlon),
              Success(maxlat)
            ) =>
          Validated.valid(Extent(minlon, minlat, maxlon, maxlat))
        case _ => Validated.invalidNel(s"Invalid extent: $string")
      }
    }

    def defaultMetavar = "minlon,minlat,maxlon,maxlat"
  }

  private implicit val urlArgument: Argument[Url] = new Argument[Url] {
    def read(string: String) = {
      Url.parseTry(string) match {
        case Success(url) => Validated.valid(url)
        case Failure(e)   => Validated.invalidNel(e.getMessage)
      }
    }

    def defaultMetavar = "url"
  }
}
