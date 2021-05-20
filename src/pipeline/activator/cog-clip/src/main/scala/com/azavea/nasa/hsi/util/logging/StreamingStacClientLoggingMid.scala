package com.azavea.nasa.hsi.util.logging

import cats.effect.Sync
import com.azavea.stac4s.api.client.{SearchFilters, StreamingStacClient, StreamingStacClientF}
import com.azavea.stac4s.{StacCollection, StacItem}
import eu.timepit.refined.types.string.NonEmptyString
import fs2.Stream
import io.chrisdavenport.log4cats.slf4j.Slf4jLogger
import io.circe.syntax._
import tofu.higherKind.Mid

final class StreamingStacClientLoggingMid[F[_]: Sync] extends StreamingStacClientF[F, Mid[Stream[F, *], *], SearchFilters] {
  val logger = Slf4jLogger.getLoggerFromClass(this.getClass)

  def search: Mid[Stream[F, *], StacItem] =
    res =>
      Stream.eval(logger.trace("streaming search all endpoint call")) >>
      res.evalTap(item => logger.trace(s"retrieved item: ${item.asJson}"))

  def search(filter: SearchFilters): Mid[Stream[F, *], StacItem] =
    res =>
      Stream.eval(logger.trace(s"streaming search ${filter.asJson} endpoint call")) >>
      res.evalTap(item => logger.trace(s"retrieved item: ${item.asJson}"))

  def collections: Mid[Stream[F, *], StacCollection] =
    res =>
      Stream.eval(logger.trace("collections all endpoint call")) >>
      res.evalTap(item => logger.trace(s"retrieved collection: ${item.asJson}"))

  def items(collectionId: NonEmptyString): Mid[Stream[F, *], StacItem] =
    res =>
      Stream.eval(logger.trace(s"items by collectionId: $collectionId endpoint call")) >>
      res.evalTap(item => logger.trace(s"retrieved item: ${item.asJson}"))

  def collection(collectionId: NonEmptyString): F[StacCollection] = ???

  def item(collectionId: NonEmptyString, itemId: NonEmptyString): F[StacItem] = ???

  def itemCreate(collectionId: NonEmptyString, item: StacItem): F[StacItem] = ???

  def collectionCreate(collection: StacCollection): F[StacCollection] = ???
}

object StreamingStacClientLoggingMid {
  def apply[F[_]: Sync]: StreamingStacClient[F, Mid[Stream[F, *], *]] = new StreamingStacClientLoggingMid[F]
}
