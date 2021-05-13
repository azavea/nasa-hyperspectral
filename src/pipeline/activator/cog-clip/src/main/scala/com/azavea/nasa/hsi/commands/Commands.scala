package com.azavea.nasa.hsi.commands

import geotrellis.util.RangeReader
import cats.{ApplicativeThrow, Parallel}
import cats.syntax.try_._
import cats.syntax.flatMap._
import cats.effect.{Concurrent, ContextShift, ExitCode}
import com.monovore.decline.{Command, Opts}
import io.chrisdavenport.log4cats.Logger
import io.circe.parser

import java.net.URI

object Commands {
  final case class RunClipCog(clipCogConfig: CogClipConfig)
  final case class RunClipCogUri(uri: URI)

  def uriToClipCog[F[_]: ApplicativeThrow](uri: URI): F[CogClipConfig] =
    parser
      .parse(RangeReader(uri).readAll().map(_.toChar).mkString)
      .flatMap(_.as[CogClipConfig])
      .toTry
      .liftTo[F]

  def runClipCog[F[_]: Concurrent: ContextShift: Parallel: Logger](clipCogConfig: CogClipConfig): F[ExitCode] =
    CogClip.runF[F](clipCogConfig)

  def runClipCogUri[F[_]: Concurrent: ContextShift: Parallel: Logger](uri: URI): F[ExitCode] =
    uriToClipCog(uri).flatMap(CogClip.runF[F])

  private def runClipCogOpts: Opts[RunClipCog] =
    Opts.subcommand("clip", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfig map RunClipCog
    }

  private def runClipCogPipelineOpts: Opts[RunClipCog] =
    Opts.subcommand("clip-pipeline", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfigJson map RunClipCog
    }

  private def runClipCogPipelineUriOpts: Opts[RunClipCogUri] =
    Opts.subcommand("clip-pipeline-uri", "Clip extents from COG as provided by GeoJSON Feature Collection") {
      Options.clipCogConfigUri map RunClipCogUri
    }

  def applicationCommand: Command[Product] =
    Command(name = "", header = "")(runClipCogPipelineUriOpts orElse runClipCogPipelineOpts orElse runClipCogOpts)
}
