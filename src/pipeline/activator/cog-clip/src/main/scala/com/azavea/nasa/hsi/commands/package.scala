package com.azavea.nasa.hsi

import cats.syntax.try_._
import cats.data.{NonEmptyList, Validated}
import com.azavea.stac4s._
import com.monovore.decline.Argument
import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector._
import geotrellis.vector.io.json.JsonFeatureCollection

import java.net.{URI, URISyntaxException}
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
