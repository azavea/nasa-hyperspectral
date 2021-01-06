package com.azavea.nasa.hsi.commands

import cats.Parallel
import com.azavea.stac4s.api.client._
import cats.effect.{Concurrent, ContextShift, ExitCode}
import cats.syntax.try_._
import cats.syntax.option._
import cats.syntax.applicative._
import cats.syntax.either._
import cats.syntax.functor._
import cats.syntax.flatMap._
import cats.effect.syntax.paralleln._
import geotrellis.raster.RasterSource
import geotrellis.raster.io.geotiff._
import geotrellis.vector.{io => _, _}
import io.chrisdavenport.log4cats.Logger
import io.circe.Json
import sttp.client3.SttpBackend
import sttp.client3.asynchttpclient.cats.AsyncHttpClientCatsBackend

import java.io.IOException
import scala.util.Try

object CogClip {

  def apply[F[_]: Concurrent: ContextShift: Parallel: Logger](config: CogClipConfig, backend: SttpBackend[F, Any]): F[ExitCode] =
    for {
      _ <- Logger[F].info(s"Retrieving item ${config.itemId} from the catalog ${config.collectionId}")
      client = SttpStacClient(backend, config.stacApiURI.toSttpUri)
      item <- client.item(config.collectionId, config.itemId)
      result <- item match {
        case Some(item) if item.assets.isDefinedAt(config.assetId.value) =>
          val asset = item.assets(config.assetId.value)
          val rs    = RasterSource(asset.href)

          config.features
            .getAllFeatures[Feature[Geometry, Json]]
            .toList
            .parTraverseN(config.threads.value) { feature =>
              Try(feature.geom.extent)
                .liftTo[F]
                .flatMap { extent =>
                  rs.read(extent)
                    .liftTo[F](new IOException(s"Could not read the requested window: $extent"))
                }
                .map(MultibandGeoTiff(_, rs.crs, GeoTiffOptions(Deflate)))
                .flatMap { geotiff =>
                  geotiff.write(config.cogAssetHref, optimizedOrder = true)
                  val cogItem = DefaultCollection.from(config, item.id, geotiff)

                  Logger[F].trace(s"POST ${cogItem.id} to ${config.stacApiURI}") >>
                  client.itemCreate(config.collectionId, cogItem)
                }
            }
            .map(_.asRight)

        case Some(item) => s"No assets found for the requested item: $item".asLeft.pure
        case _          => s"No requested item found: ${(config.collectionId, config.itemId)}".asLeft.pure
      }
    } yield result.fold(_ => ExitCode.Error, _ => ExitCode.Success)

  def runF[F[_]: Concurrent: ContextShift: Parallel: Logger](config: CogClipConfig): F[ExitCode] =
    AsyncHttpClientCatsBackend.resource[F]().use(apply(config, _))
}
