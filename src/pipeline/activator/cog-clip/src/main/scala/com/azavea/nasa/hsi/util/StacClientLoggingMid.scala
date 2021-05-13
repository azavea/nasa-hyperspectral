package com.azavea.nasa.hsi.util

import com.azavea.stac4s.{StacCollection, StacItem}
import com.azavea.stac4s.api.client.{SearchFilters, StacClient, StacClientF}

import cats.effect.Sync
import cats.syntax.flatMap._
import tofu.higherKind.Mid
import eu.timepit.refined.types.string.NonEmptyString
import io.chrisdavenport.log4cats.slf4j.Slf4jLogger
import io.circe.syntax._

final class StacClientLoggingMid[F[_]: Sync] extends StacClientF[Mid[F, *], SearchFilters] {
  val logger = Slf4jLogger.getLoggerFromClass(this.getClass)

  def search: Mid[F, List[StacItem]] =
    res =>
      logger.trace(s"search all endpoint call") >>
      res.flatTap(items => logger.trace(s"retrieved items: ${items.asJson}"))

  def search(filter: SearchFilters): Mid[F, List[StacItem]] =
    res =>
      logger.trace(s"search ${filter.asJson} endpoint call") >>
      res.flatTap(items => logger.trace(s"retrieved items: ${items.asJson}"))

  def collections: Mid[F, List[StacCollection]] =
    res =>
      logger.trace(s"collections all endpoint call") >>
      res.flatTap(collections => logger.trace(s"retrieved collections: ${collections.asJson}"))

  def collection(collectionId: NonEmptyString): Mid[F, StacCollection] =
    res =>
      logger.trace(s"collections collectionId: $collectionId endpoint call") >>
      res.flatTap(collection => logger.trace(s"retrieved collection: ${collection.asJson}"))

  def items(collectionId: NonEmptyString): Mid[F, List[StacItem]] =
    res =>
      logger.trace(s"items by collectionId: $collectionId endpoint call") >>
      res.flatTap(items => logger.trace(s"retrieved items: ${items.asJson}"))

  def item(collectionId: NonEmptyString, itemId: NonEmptyString): Mid[F, StacItem] =
    res =>
      logger.trace(s"item by collectionId: $collectionId and itemId: $itemId endpoint call") >>
      res.flatTap(items => logger.trace(s"retrieved items: ${items.asJson}"))

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
  def apply[F[_]: Sync]: StacClient[Mid[F, *]] = new StacClientLoggingMid[F]
}
