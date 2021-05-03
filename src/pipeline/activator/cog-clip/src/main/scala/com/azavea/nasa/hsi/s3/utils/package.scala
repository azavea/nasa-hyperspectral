package com.azavea.nasa.hsi.s3

import cats.effect.Sync
import geotrellis.raster.CellGrid
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.store.s3.AmazonS3URI
import geotrellis.store.s3._

package object utils {
  implicit class GeoTiffS3WriteMethods[T <: CellGrid[Int]](val self: GeoTiff[T]) extends AnyVal {
    def writeF[F[_]: Sync](uri: AmazonS3URI): F[Unit] = Sync[F].delay(self.write(uri))
  }
}
