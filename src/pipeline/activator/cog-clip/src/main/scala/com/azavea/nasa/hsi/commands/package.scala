package com.azavea.nasa.hsi

import cats.MonadError
import cats.syntax.try_._
import cats.data.{NonEmptyList, Validated}
import com.azavea.stac4s._
import com.monovore.decline.Argument
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.raster.geotiff.GeoTiffPath
import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector.{io => _, _}
import geotrellis.vector.io.json.JsonFeatureCollection
import io.circe.Decoder.Result
import io.circe.Json
import io.circe.refined._

import java.net.{URI, URISyntaxException}
import java.util.UUID
import scala.util.Try

package object commands {

  implicit class ExtentOps(val self: Extent) extends AnyVal {
    def toTwoDimBbox: TwoDimBbox = {
      val Extent(xmin, xmax, ymin, ymax) = self
      TwoDimBbox(xmin, xmax, ymin, ymax)
    }
  }

  implicit class URIOps(val self: URI) extends AnyVal {
    import sttp.client3.UriContext
    def toSttpUri: sttp.model.Uri = uri"$self"
  }

  implicit class JsonOps(val self: Json) extends AnyVal {
    def id: Result[NonEmptyString]                                = self.hcursor.downField("id").as[NonEmptyString]
    def idF[F[_]: MonadError[*[_], Throwable]]: F[NonEmptyString] = MonadError[F, Throwable].fromTry(id.toTry)
    def randomIdF[F[_]: MonadError[*[_], Throwable]]: F[NonEmptyString] =
      MonadError[F, Throwable].pure(id.fold(_ => NonEmptyString.unsafeFrom(UUID.randomUUID().toString), identity))
  }

  implicit class StacItemAssetOps(val self: StacItemAsset) extends AnyVal {
    def hrefGDAL(withGDAL: Boolean): String = if (withGDAL) s"gdal+${self.href}" else s"${GeoTiffPath.PREFIX}${self.href}"
  }

  implicit val featureCollectionArgument: Argument[JsonFeatureCollection] =
    Argument.from("""{ "type": "FeatureCollection", "features": [<features>] }""") { string =>
      Try(string.stripMargin.parseGeoJson[JsonFeatureCollection]).toValidated
        .leftMap(e => NonEmptyList.one(e.getMessage))
    }

  implicit val readAmazonS3URI: Argument[AmazonS3URI] =
    Argument.from("Amazon S3 URI") { string =>
      try Validated.valid(new AmazonS3URI(new URI(string)))
      catch {
        case use: URISyntaxException =>
          Validated.invalidNel(s"Invalid AmazonS3URI: $string (${use.getReason})")
        case use: IllegalArgumentException =>
          Validated.invalidNel(s"Invalid AmazonS3URI: $string (${use.getMessage})")
      }
    }
}
