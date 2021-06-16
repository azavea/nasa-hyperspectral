package com.azavea.nasa.hsi.commands

import geotrellis.util.RangeReader
import cats.{ApplicativeThrow, Parallel}
import cats.syntax.try_._
import cats.syntax.flatMap._
import cats.effect.{Concurrent, ContextShift, ExitCode}
import com.monovore.decline.{Command, Opts}
import io.chrisdavenport.log4cats.Logger
import io.circe.parser

object Commands {
  final case class RunCogClip(cogClipConfig: CogClipConfig)
  final case class RunCogClipUri(cogClipUriConfig: CogClipUriConfig)

  def uriToCogClip[F[_]: ApplicativeThrow](cogClipUriConfig: CogClipUriConfig): F[CogClipConfig] =
    parser
      .parse(RangeReader(cogClipUriConfig.uri).readAll().map(_.toChar).mkString)
      .flatMap(_.as[CogClipConfig])
      .map { config =>
        val configOverride = cogClipUriConfig.cogClipConfigOverride
        config.copy(
          sourceCollectionId = configOverride.sourceCollectionId.getOrElse(config.sourceCollectionId),
          sourceItemId = configOverride.sourceItemId.getOrElse(config.sourceItemId),
          sourceAssetId = configOverride.sourceAssetId.getOrElse(config.sourceAssetId)
        )
      }
      .toTry
      .liftTo[F]

  def runCogClip[F[_]: Concurrent: ContextShift: Parallel: Logger](cogClipConfig: CogClipConfig): F[ExitCode] =
    CogClip.runF[F](cogClipConfig)

  def runCogClipUri[F[_]: Concurrent: ContextShift: Parallel: Logger](cogClipUriConfig: CogClipUriConfig): F[ExitCode] =
    uriToCogClip(cogClipUriConfig).flatMap(CogClip.runF[F])

  private def runCogClipOpts: Opts[RunCogClip] =
    Opts.subcommand("clip", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.cogClipConfig map RunCogClip
    }

  private def runCogClipPipelineOpts: Opts[RunCogClip] =
    Opts.subcommand("clip-pipeline", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.cogClipConfigJson map RunCogClip
    }

  private def runClipCogPipelineUriOpts: Opts[RunCogClipUri] =
    Opts.subcommand("clip-pipeline-uri", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.cogClipUriConfig map RunCogClipUri
    }

  def applicationCommand: Command[Product] =
    Command(name = "", header = "")(runClipCogPipelineUriOpts orElse runCogClipPipelineOpts orElse runCogClipOpts)
}
