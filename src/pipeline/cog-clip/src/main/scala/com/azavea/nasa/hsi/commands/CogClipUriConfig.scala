package com.azavea.nasa.hsi.commands

import eu.timepit.refined.types.string.NonEmptyString
import io.circe.generic.JsonCodec
import io.circe.refined._

import java.net.URI

@JsonCodec
case class CogClipUriConfig(
  uri: URI,
  cogClipConfigOverride: CogClipConfigOverride
)

@JsonCodec
case class CogClipConfigOverride(
  sourceCollectionId: Option[NonEmptyString],
  sourceItemId: Option[NonEmptyString],
  sourceAssetId: Option[NonEmptyString]
)
