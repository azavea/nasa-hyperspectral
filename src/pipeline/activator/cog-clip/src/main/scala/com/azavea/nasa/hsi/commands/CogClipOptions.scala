package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts
import com.monovore.decline.refined._
import cats.syntax.apply._
import eu.timepit.refined.types.all.PosInt
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector.io.json.JsonFeatureCollection

import java.net.URI

trait CogClipOptions {

  private val sourceCollectionId = Opts.option[NonEmptyString](long = "source-collection-id", help = "Source collectionId.")

  private val sourceItemId = Opts.option[NonEmptyString](long = "source-item-id", help = "Source itemId.")

  private val sourceAssetId = Opts.option[NonEmptyString](long = "source-asset-id", help = "Source assetIt.")

  private val targetCollectionId = Opts.option[NonEmptyString](long = "target-collection-id", help = "Target collectionId.")

  private val targetLayerId: Opts[Option[NonEmptyString]] =
    Opts
      .option[NonEmptyString](long = "target-layer-id", help = "Target layerId.")
      .orNone

  private val features =
    Opts
      .option[JsonFeatureCollection](long = "features", help = "Feature Collection of features to clip from COG")
      .orElse(Opts.env[JsonFeatureCollection](name = "FEATURES", help = "Feature Collection of features to clip from COG."))

  private val stacApiURI =
    Opts
      .option[URI](long = "stac-api-uri", help = "")
      .orElse(Opts.env[URI](name = "STAC_API_URI", help = ""))
      .withDefault(new URI("http://localhost:9090"))

  private val targetS3URI =
    Opts
      .option[AmazonS3URI](long = "target-s3-uri", help = "")
      .orElse(Opts.env[AmazonS3URI](name = "TARGET_S3_URI", help = ""))
      .withDefault(new AmazonS3URI("s3://nasahyperspectral-test/activator-clip-cogs/"))

  private val threads =
    Opts
      .option[PosInt](long = "threads", help = "Number of threads")
      .orElse(Opts.env[PosInt](name = "THREADS", help = "Number of threads."))
      .withDefault(PosInt.unsafeFrom(Runtime.getRuntime.availableProcessors))

  private val withGDAL = Opts.flag(long = "with-gdal", help = "Uses GDAL for raster reads.").orFalse

  private val force = Opts.flag(long = "force", help = "Force reingest StacItem even though this it is already present in the catalog.").orFalse

  val cogClipConfig: Opts[CogClipConfig] =
    (
      sourceCollectionId,
      sourceItemId,
      sourceAssetId,
      targetCollectionId,
      targetLayerId,
      features,
      stacApiURI,
      targetS3URI,
      threads,
      withGDAL,
      force
    ) mapN CogClipConfig.apply
}
