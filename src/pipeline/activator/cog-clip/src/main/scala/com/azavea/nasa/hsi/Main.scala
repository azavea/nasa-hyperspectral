package com.azavea.nasa.hsi

import cats.effect.{ExitCode, IO, IOApp}
import com.azavea.nasa.hsi.commands.Commands
import io.chrisdavenport.log4cats.Logger
import io.chrisdavenport.log4cats.slf4j.Slf4jLogger

object Main extends IOApp {
  def run(args: List[String]): IO[ExitCode] = {
    implicit val logger: Logger[IO] = Slf4jLogger.getLogger[IO]

    import Commands._
    applicationCommand.parse(args, env = sys.env) map { case RunClipCog(config) =>
      Commands.runClipCog[IO](config)
    } match {
      case Left(e)  => logger.error(e.toString()).as(ExitCode.Error)
      case Right(s) => s
    }
  }
}
