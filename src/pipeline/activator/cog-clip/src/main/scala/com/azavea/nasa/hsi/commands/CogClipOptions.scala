package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts
import com.monovore.decline.refined._
import cats.syntax.apply._
import eu.timepit.refined.types.string.NonEmptyString
import geotrellis.vector.io.json.JsonFeatureCollection
import io.lemonlabs.uri.Url

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

  private val stacApiUrl =
    Opts
      .option[Url](long = "stac-api-url", help = "")
      .orElse(
        Opts
          .env[Url](name = "STAC_API_URL", help = "")
          .withDefault(Url.parse("http://localhost:9090"))
      )

  private val targetS3Bucket =
    Opts
      .option[NonEmptyString](long = "target-s3-bucket", help = "")
      .orElse(
        Opts
          .env[NonEmptyString]("ACC_TARGET_S3_BUCKET", help = "")
          .withDefault(NonEmptyString("nasa-hsi-activator-clip-cogs"))
      )

  val clipCogConfig: Opts[CogClipConfig] =
    (
      assetId,
      collectionId,
      features,
      itemId,
      stacApiUrl,
      targetS3Bucket
    ) mapN CogClipConfig
}
