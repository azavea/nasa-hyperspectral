package com.azavea.nasa.hsi.util.logging

import com.azavea.nasa.hsi.util._

import cats.effect.Sync
import cats.syntax.flatMap._
import com.azavea.stac4s.api.client.{SearchFilters, StreamingStacClient, StreamingStacClientF, StreamingStacClientFS2}
import com.azavea.stac4s.{StacCollection, StacItem}
import eu.timepit.refined.types.string.NonEmptyString
import fs2.Stream
import io.chrisdavenport.log4cats.slf4j.Slf4jLogger
import io.circe.syntax._
import tofu.higherKind.Mid

final class StacClientLoggingMid[F[_]: Sync] extends StreamingStacClientF[Mid[F, *], Stream[F, *], SearchFilters] {
  val logger = Slf4jLogger.getLoggerFromClass(this.getClass)

  def search: Stream[F, StacItem] = Stream.empty

  def search(filter: SearchFilters): Stream[F, StacItem] = Stream.empty

  def collections: Stream[F, StacCollection] = Stream.empty

  def items(collectionId: NonEmptyString): Stream[F, StacItem] = Stream.empty

  def collection(collectionId: NonEmptyString): Mid[F, StacCollection] =
    res =>
      logger.trace(s"collections collectionId: $collectionId endpoint call") >>
      res.flatTap(collection => logger.trace(s"retrieved collection: ${collection.asJson}"))

  def item(collectionId: NonEmptyString, itemId: NonEmptyString): Mid[F, StacItem] =
    res =>
      logger.trace(s"item by collectionId: $collectionId and itemId: $itemId endpoint call") >>
      res.flatTap(item => logger.trace(s"retrieved item: ${item.asJson}"))

  def itemCreate(collectionId: NonEmptyString, item: StacItem): Mid[F, StacItem] =
    res =>
      logger.trace(s"itemCreate for collectionId: $collectionId and item: $item") >>
      res.flatTap(item => logger.trace(s"created item: ${item.asJson}"))

  def collectionCreate(collection: StacCollection): Mid[F, StacCollection] =
    res =>
      logger.trace(s"collectionCreate of collection: $collection") >>
      res.flatTap(collection => logger.trace(s"created collection: ${collection.asJson}"))
}

object StacClientLoggingMid {
  def apply[F[_]: Sync]: StreamingStacClient[Mid[F, *], Stream[F, *]] = new StacClientLoggingMid[F]

  def attachAll[F[_]: Sync](client: StreamingStacClientFS2[F]): StreamingStacClientFS2[F] =
    Mid
      .attach[StreamingStacClient[*[_], fs2.Stream[F, *]], F](StacClientLoggingMid[F])(
        Mid.attach(StreamingStacClientLoggingMid[F])(client)
      )
}
