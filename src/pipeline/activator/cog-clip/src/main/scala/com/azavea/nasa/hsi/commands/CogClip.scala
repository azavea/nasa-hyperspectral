package com.azavea.nasa.hsi.commands

import com.azavea.nasa.hsi.util._
import com.azavea.nasa.hsi.util.s3._

import cats.Parallel
import com.azavea.stac4s.api.client._
import cats.effect.{Concurrent, ContextShift, ExitCode, Sync}
import cats.syntax.try_._
import cats.syntax.option._
import cats.syntax.applicativeError._
import cats.syntax.either._
import cats.syntax.applicative._
import cats.syntax.functor._
import cats.syntax.flatMap._
import cats.effect.syntax.paralleln._
import com.azavea.stac4s.StacItem
import geotrellis.proj4.LatLng
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff._
import geotrellis.vector.{io => _, _}
import io.chrisdavenport.log4cats.Logger
import io.circe.Json
import sttp.client3.{HttpError, SttpBackend}
import sttp.client3.asynchttpclient.cats.AsyncHttpClientCatsBackend
import sttp.model.StatusCode

import java.io.IOException
import scala.util.Try

object CogClip {

  def apply[F[_]: Concurrent: ContextShift: Parallel: Logger](config: CogClipConfig, backend: SttpBackend[F, Any]): F[ExitCode] =
    for {
      _ <- Logger[F].info(s"Retrieving item ${config.sourceItemId} from the catalog ${config.sourceCollectionId}...")
      client = SttpStacClient(backend, config.stacApiURI.toSttpUri).withLogging
      // request an item
      item <- client
        .item(config.sourceCollectionId, config.sourceItemId)
        .redeem({ case e: HttpError[_] if e.statusCode == StatusCode.NotFound => None }, _.some)
      result <- item match {
        // if such item is present in the catalog
        case Some(item) if item.assets.isDefinedAt(config.sourceAssetId.value) =>
          val asset = item.assets(config.sourceAssetId.value)
          val rs    = RasterSource(asset.hrefGDAL(config.withGDAL))

          // traverse through all input features and window read each geometry
          config.features
            .getAllFeatures[Feature[Geometry, Json]]
            .toList
            .parTraverseN(config.threads.value) { feature =>
              // check if feature is already present in the target collection
              feature.data
                .randomIdF[F]
                .flatMap { featureId =>
                  client
                    .item(config.targetCollectionId, config.resultId(featureId))
                    .redeem({ case e: HttpError[_] if e.statusCode == StatusCode.NotFound => None }, _.some)
                }
                .flatMap {
                  // if the target item is already present in the target collection, than do nothing
                  case Some(oldItem) if !config.force =>
                    Logger[F]
                      .trace(s"Item ${oldItem.id} is already present in the collection ${config.targetCollectionId}")
                      .as(oldItem)
                  // if it is new, read and write tiff
                  case _ =>
                    Try(feature.geom.extent.reproject(LatLng, rs.crs))
                      .liftTo[F]
                      .flatMap { extent =>
                        Logger[F].trace(s"Reading the window: $extent") >>
                        rs.read(extent)
                          .liftTo[F](new IOException(s"Could not read the requested window: $extent"))
                      }
                      .flatTap(_ => Logger[F].trace("Building GeoTIFF..."))
                      .map(MultibandGeoTiff(_, rs.crs, GeoTiffOptions(Deflate)))
                      .flatMap(tiffWrite(config, feature, item, _, client))
                }
            }
            .map(_.asRight)
            .flatTap(_ => Logger[F].info("Done!"))

        case Some(item) =>
          val msg = s"No assets found for the requested item: $item"
          Logger[F].error(msg).as(msg.asLeft)
        case _ =>
          val msg = s"No requested item found with collectionId ${config.sourceCollectionId} and Id: ${config.sourceItemId}"
          Logger[F].error(msg).as(msg.asLeft)
      }
    } yield result.fold(_ => ExitCode.Error, _ => ExitCode.Success)

  private def tiffWrite[F[_]: Sync: Logger](
    config: CogClipConfig,
    feature: Feature[Geometry, Json],
    item: StacItem,
    geotiff: MultibandGeoTiff,
    client: StacClient[F]
  ): F[StacItem] =
    feature.data.randomIdF[F].flatMap { featureId =>
      // write tiff
      Logger[F].trace(s"Writing tiff to ${config.cogAssetHrefPath(featureId)}") >>
      geotiff.writeF(config.cogAssetHrefPath(featureId)) >>
      // create [[StacItem]] and insert it into the target collection
      // it creates the target collection if it's missing
      DefaultCollection
        .item(config, featureId, item, feature.geom)
        .pure
        .flatMap { cogItem =>
          for {
            _ <- Logger[F].trace(s"Create if doesn't exists a default target AVIRIS ${config.targetCollectionId} collection")
            _ <- client
              .collectionCreate(DefaultCollection.collection(config.targetCollectionId.value))
              .onError { case _ => Logger[F].trace(s"Collection ${config.targetCollectionId} already exists") }
            _ <- Logger[F].trace(s"Create Item ${cogItem.id} int the collection ${config.targetCollectionId}")
            item <- client
              .itemCreate(config.targetCollectionId, cogItem)
              .onError { case _ =>
                Logger[F].trace(s"Item ${cogItem.id} already exists in the collection ${config.targetCollectionId}")
              }
          } yield item
        }
    }

  def runF[F[_]: Concurrent: ContextShift: Parallel: Logger](config: CogClipConfig): F[ExitCode] =
    AsyncHttpClientCatsBackend.resource[F]().use(apply(config, _))
}
