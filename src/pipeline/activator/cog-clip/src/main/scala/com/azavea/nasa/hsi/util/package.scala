package com.azavea.nasa.hsi

import cats.tagless.{ApplyK, Derive}
import com.azavea.stac4s.api.client.StacClient

package object util {
  implicit val stacClientApplyK: ApplyK[StacClient] = Derive.applyK
}
