package com.azavea.nasa.hsi.commands

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
import com.azavea.nasa.hsi.s3.S3Configuration
import com.azavea.stac4s.StacItem
import geotrellis.proj4.LatLng
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff._
import geotrellis.vector.{io => _, _}
import geotrellis.store.hadoop._
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
      _ <- Logger[F].info(s"Retrieving item ${config.sourceItemId} from the catalog ${config.sourceCollectionId}")
      client = SttpStacClient(backend, config.stacApiURI.toSttpUri)
      // request an item
      item <- client.item(config.sourceCollectionId, config.sourceItemId)
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
              // check if features is already present in the target collection
              feature.data
                .randomIdF[F]
                .flatMap { featureId =>
                  client
                    .item(config.targetCollectionId, config.resultId(featureId))
                    .recoverWith {
                      case e: HttpError[_] if e.statusCode == StatusCode.NotFound =>
                        Logger[F]
                          .trace(s"Item ${config.resultId(featureId)} doesn't exist in the collection ${config.targetCollectionId}")
                          .as(None)
                    }
                }
                .flatMap {
                  // if the target item is already present in the target collection, than do nothing
                  case Some(oldItem) =>
                    Logger[F]
                      .info(s"Item ${oldItem.id} is already present in the collection ${config.targetCollectionId}")
                      .as(oldItem)
                  // if it is new, read and write tiff
                  case _ =>
                    Try(feature.geom.extent.reproject(LatLng, rs.crs))
                      .liftTo[F]
                      .flatMap { extent =>
                        rs.read(extent)
                          .liftTo[F](new IOException(s"Could not read the requested window: $extent"))
                      }
                      .map(MultibandGeoTiff(_, rs.crs, GeoTiffOptions(Deflate)))
                      .flatMap(tiffWrite(config, feature, item, _, client))
                }
            }
            .map(_.asRight)

        case Some(item) => s"No assets found for the requested item: $item".asLeft.pure
        case _          => s"No requested item found: ${(config.sourceCollectionId, config.sourceItemId)}".asLeft.pure
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
      Logger[F].trace(s"Writing tiff to ${config.cogAssetHrefLocal(featureId)}") >>
      S3Configuration.defaultSync[F].map(geotiff.write(config.cogAssetHrefLocal(featureId), _)) >>
      // create [[StacItem]] and insert it into the target collection
      // it creates the target collection if it's missing
      DefaultCollection
        .item(config, featureId, item.id, feature.geom)
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
