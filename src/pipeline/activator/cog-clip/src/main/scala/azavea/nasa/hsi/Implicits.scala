package azavea.nasa.hsi

import cats.data.Validated
import com.azavea.stac4s.TwoDimBbox
import com.monovore.decline._
import geotrellis.vector.Extent
import geotrellis.vector.io.json._
import geotrellis.vector.io.json.Implicits._
import io.lemonlabs.uri.Url

import scala.util.{Failure, Success, Try}

trait Implicits {

  implicit def extentToTwoDimBbox(e: Extent): TwoDimBbox =
    TwoDimBbox(e.xmin, e.ymin, e.xmax, e.ymax)

  implicit def extentArgument: Argument[Extent] = new Argument[Extent] {
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

  implicit def featureCollectionArgument
      : Argument[JsonFeatureCollection] = new Argument[JsonFeatureCollection] {

    def read(string: String) = {
      try {
        val features = string.stripMargin.parseGeoJson[JsonFeatureCollection]
        Validated.valid(features)
      } catch {
        case e: Exception => Validated.invalidNel(e.toString)
      }
    }

    def defaultMetavar =
      "{ \"type\": \"FeatureCollection\", \"features\": [<features>] }"
  }

  implicit def urlArgument: Argument[Url] = new Argument[Url] {
    def read(string: String) = {
      Url.parseTry(string) match {
        case Success(url) => Validated.valid(url)
        case Failure(e)   => Validated.invalidNel(e.getMessage)
      }
    }

    def defaultMetavar = "url"
  }
}
