package azavea.nasa.hsi

import cats.effect.{ExitCode, IO}

import com.monovore.decline._
import com.monovore.decline.effect._

/** TODO:
  * - [ ] Refactor to use FeatureCollection of geoms to clip multiple items
  * - [x] Refactor to use s"$sourceCollection-$sourceFeatureId" as Clipped COG STAC Item ID
  * - [x] Refactor to use github.com/azavea/azavea.g8 Commands template:
  *       https://github.com/azavea/azavea.g8/blob/master/src/main/g8/application/src/main/scala/%24package__packaged%24/api/commands/Commands.scala
  * - [ ] https://github.com/azavea/nasa-hyperspectral/issues/80 and then use here
  */

object Main
    extends CommandIOApp(
      name = "clip",
      header = "Clip extents from COG as provided by GeoJSON Feature Collection"
    ) {

  override def main: Opts[IO[ExitCode]] =
    (Options.clipCogConfig) map Commands.clipCog
}
