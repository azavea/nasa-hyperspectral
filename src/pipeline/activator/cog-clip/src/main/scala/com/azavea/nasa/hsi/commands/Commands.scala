package com.azavea.nasa.hsi.commands

import cats.effect.{ContextShift, ExitCode, IO}
import com.monovore.decline.{Command, Opts}
import io.chrisdavenport.log4cats.Logger

object Commands {
  final case class RunClipCog(clipCogConfig: CogClipConfig)

  def runClipCog(clipCogConfig: CogClipConfig)(implicit cs: ContextShift[IO], logger: Logger[IO]): IO[ExitCode] =
    CogClip.runF[IO](clipCogConfig)

  private def runClipCogOpts(implicit cs: ContextShift[IO]): Opts[RunClipCog] =
    Opts.subcommand("clip", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfig map RunClipCog
    }

  def applicationCommand(implicit cs: ContextShift[IO]): Command[Product] =
    Command(name = "", header = "")(runClipCogOpts)
}
