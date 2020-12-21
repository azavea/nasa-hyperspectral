package azavea.nasa

import cats.data.Validated
import cats.implicits._
import com.azavea.stac4s._
import com.azavea.stac4s.types._
import com.monovore.decline._
import geotrellis.vector.Extent
import io.circe.syntax._
import io.lemonlabs.uri.Url

import java.time.Instant
import scala.util.{Failure, Success, Try}

package object hsi {

  val HsiStacVersion = "1.0.0-beta.2"

  implicit val extentArgument: Argument[Extent] = new Argument[Extent] {
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

  implicit val urlArgument: Argument[Url] = new Argument[Url] {
    def read(string: String) = {
      Url.parseTry(string) match {
        case Success(url) => Validated.valid(url)
        case Failure(e)   => Validated.invalidNel(e.getMessage)
      }
    }

    def defaultMetavar = "url"
  }

  implicit def extentToTwoDimBbox(e: Extent): TwoDimBbox =
    TwoDimBbox(e.xmin, e.ymin, e.xmax, e.ymax)

  private val cogCollectionId = "nasa-hsi-activator-cog-clip"
  private val JAN_1_2006_EPOCH = 1136073600
  private val JAN_1_2020_EPOCH = 1577836800
  private val initialCogCollectionExtent = StacExtent(
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
          Instant.ofEpochSecond(JAN_1_2006_EPOCH),
          Instant.ofEpochSecond(JAN_1_2020_EPOCH)
        )
      )
    )
  )
  val CogClipCollection = StacCollection(
    HsiStacVersion,
    List.empty[String],
    cogCollectionId,
    Some(""),
    "A STAC Collection containing COGs created by the nasa-hsi cog-clip activator",
    List.empty[String],
    Proprietary(),
    List.empty[StacProvider],
    initialCogCollectionExtent,
    Map.empty[String, String].asJsonObject,
    Map.empty[String, String].asJsonObject,
    List.empty[StacLink],
    Map.empty[String, String].asJsonObject
  )
}
