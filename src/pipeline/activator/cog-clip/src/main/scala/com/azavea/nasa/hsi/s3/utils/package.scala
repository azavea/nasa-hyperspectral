package com.azavea.nasa.hsi.s3

import cats.effect.Sync
import geotrellis.raster.CellGrid
import geotrellis.raster.io.geotiff.GeoTiff
import geotrellis.store.s3.{AmazonS3URI, S3ClientProducer}
import software.amazon.awssdk.core.sync.RequestBody
import software.amazon.awssdk.services.s3.model.PutObjectRequest

package object utils {
  implicit class GeoTiffS3WriteMethods[T <: CellGrid[Int]](val self: GeoTiff[T]) extends AnyVal {
    def write(uri: AmazonS3URI): Unit = {
      val client = S3ClientProducer.get()
      val objectRequest = PutObjectRequest.builder
        .bucket(uri.getBucket)
        .key(uri.getKey)
        .build

      client.putObject(objectRequest, RequestBody.fromBytes(self.toCloudOptimizedByteArray))
    }

    def writeF[F[_]: Sync](uri: AmazonS3URI): F[Unit] = Sync[F].delay(write(uri))
  }
}
