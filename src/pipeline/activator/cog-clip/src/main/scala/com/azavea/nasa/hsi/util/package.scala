package com.azavea.nasa.hsi

import cats.effect.Sync
import fs2.Stream
import cats.tagless.{ApplyK, Derive}
import com.azavea.nasa.hsi.util.logging.StacClientLoggingMid
import com.azavea.stac4s.api.client.{StreamingStacClientFS2, StreamingStacClient}

package object util {
  implicit def stacClientApplyK[F[_]]: ApplyK[StreamingStacClient[*[_], Stream[F, *]]] = Derive.applyK
  implicit def streamingStacClientApplyK[F[_]]: ApplyK[StreamingStacClient[F, *[_]]]   = Derive.applyK

  implicit class StreamingStacClientOps[F[_]](val self: StreamingStacClientFS2[F]) extends AnyVal {
    def withLogging(implicit sync: Sync[F]): StreamingStacClientFS2[F] = StacClientLoggingMid.attachAll(self)
  }
}
