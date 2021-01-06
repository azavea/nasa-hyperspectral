package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts
import com.monovore.decline.refined._
import cats.syntax.apply._
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.store.s3.AmazonS3URI
import geotrellis.vector.io.json.JsonFeatureCollection

import java.net.URI

trait CogClipOptions {

  private val assetId = Opts.argument[NonEmptyString]("stac-asset-id")

  private val collectionId = Opts.argument[NonEmptyString]("collection-id")

  private val features =
    Opts
      .option[JsonFeatureCollection](long = "features", help = "Feature Collection of features to clip from COG")
      .orElse(
        Opts
          .env[JsonFeatureCollection](name = "ACC_FEATURES", help = "Feature Collection of features to clip from COG")
      )

  private val itemId = Opts.argument[NonEmptyString]("stac-item-id")

  private val stacApiURI =
    Opts
      .option[URI](long = "stac-api-uri", help = "")
      .orElse(
        Opts
          .env[URI](name = "STAC_API_URI", help = "")
          .withDefault(new URI("http://localhost:9090"))
      )

  private val targetS3URI =
    Opts
      .option[AmazonS3URI](long = "target-s3-uri", help = "")
      .orElse(
        Opts
          .env[AmazonS3URI]("ACC_TARGET_S3_URI", help = "")
          .withDefault(new AmazonS3URI("s3://nasahyperspectral-test/activator-clip-cogs/"))
      )

  val clipCogConfig: Opts[CogClipConfig] =
    (
      assetId,
      collectionId,
      itemId,
      features,
      stacApiURI,
      targetS3URI
    ) mapN CogClipConfig
}
