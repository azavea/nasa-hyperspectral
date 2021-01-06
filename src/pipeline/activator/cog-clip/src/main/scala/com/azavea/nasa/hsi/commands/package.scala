package com.azavea.nasa.hsi

import cats.syntax.try_._
import cats.syntax.traverse._
import cats.data.{NonEmptyList, Validated}
import com.azavea.stac4s._
import com.monovore.decline.Argument
import geotrellis.vector.{io => _, _}
import geotrellis.vector.io.json.JsonFeatureCollection
import io.lemonlabs.uri.{Uri, Url}

import scala.util.{Success, Try}

package object commands {

  implicit class ExtentOps(val self: Extent) extends AnyVal {
    def toTwoDimBbox: TwoDimBbox = {
      val Extent(xmin, xmax, ymin, ymax) = self
      TwoDimBbox(xmin, xmax, ymin, ymax)
    }
  }

  implicit class UriOps(val self: Uri) extends AnyVal {
    import sttp.client3.UriContext
    def toSttpUri: sttp.model.Uri = uri"${self.toStringRaw}"
  }

  implicit val extentArgument: Argument[Extent] =
    Argument.from("minlon, minlat, maxlon, maxlat // xmin, ymin, xmax, ymax") { string =>
      string
        .split(",")
        .map(_.trim)
        .toList
        .traverse(d => Try(d.toDouble)) match {
        case Success(List(xmin, ymin, xmax, ymax)) =>
          Validated.valid(Extent(xmin, ymin, xmax, ymax))
        case _ => Validated.invalidNel(s"Invalid extent: $string")
      }
    }

  implicit val featureCollectionArgument: Argument[JsonFeatureCollection] =
    Argument.from("""{ "type": "FeatureCollection", "features": [<features>] }""") { string =>
      Try(string.stripMargin.parseGeoJson[JsonFeatureCollection]).toValidated.leftMap(e => NonEmptyList.one(e.getMessage))
    }

  implicit val urlArgument: Argument[Url] =
    Argument.from("url") { string =>
      Url.parseTry(string).toValidated.leftMap(e => NonEmptyList.one(e.getMessage))
    }
}
