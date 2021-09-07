package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts
import com.monovore.decline.refined._
import eu.timepit.refined.types.string.NonEmptyString
import cats.syntax.apply._

import java.net.URI

trait CogClipUriOptions {
  private val sourceCollectionId: Opts[Option[NonEmptyString]] =
    Opts.option[NonEmptyString](long = "source-collection-id", help = "Source collectionId.").orNone

  private val sourceItemId: Opts[Option[NonEmptyString]] =
    Opts.option[NonEmptyString](long = "source-item-id", help = "Source itemId.").orNone

  private val sourceAssetId: Opts[Option[NonEmptyString]] =
    Opts.option[NonEmptyString](long = "source-asset-id", help = "Source assetIt.").orNone

  private val cogClipConfigUri: Opts[URI] = Opts.option[URI](long = "uri", help = "JSON that sets application arguments.")

  private val cogClipConfigOverrideJson: Opts[Option[CogClipConfigOverride]] =
    Opts.option[CogClipConfigOverride](long = "override", help = "JSON that sets application arguments.").orNone

  val cogClipConfigOverride: Opts[CogClipConfigOverride] =
    (
      sourceCollectionId,
      sourceItemId,
      sourceAssetId
    ) mapN CogClipConfigOverride.apply

  val cogClipUriConfig: Opts[CogClipUriConfig] =
    (
      cogClipConfigUri,
      cogClipConfigOverrideJson,
      cogClipConfigOverride
    ) mapN { (uri, overrideJson, overrideParams) => CogClipUriConfig(uri, overrideJson.getOrElse(overrideParams)) }
}
