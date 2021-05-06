package com.azavea.nasa.hsi.commands

import cats.Parallel
import cats.effect.{Concurrent, ContextShift, ExitCode}
import com.monovore.decline.{Command, Opts}
import io.chrisdavenport.log4cats.Logger

object Commands {
  final case class RunClipCog(clipCogConfig: CogClipConfig)

  def runClipCog[F[_]: Concurrent: ContextShift: Parallel: Logger](clipCogConfig: CogClipConfig): F[ExitCode] =
    CogClip.runF[F](clipCogConfig)

  private def runClipCogOpts: Opts[RunClipCog] =
    Opts.subcommand("clip", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfig map RunClipCog
    }

  private def runClipCogPipelineOpts: Opts[RunClipCog] =
    Opts.subcommand("clip-pipeline", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfigJson map RunClipCog
    }

  def applicationCommand: Command[Product] =
    Command(name = "", header = "")(runClipCogPipelineOpts orElse runClipCogOpts)
}
