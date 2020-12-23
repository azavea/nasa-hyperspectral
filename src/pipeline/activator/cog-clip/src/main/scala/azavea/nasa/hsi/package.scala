package azavea.nasa

import com.azavea.stac4s._
import com.azavea.stac4s.types._
import geotrellis.vector.Extent
import io.circe.syntax._

import java.time.Instant

package object hsi extends Implicits {

  val HsiStacVersion = "1.0.0-beta.2"

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
