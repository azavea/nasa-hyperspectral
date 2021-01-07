package com.azavea.nasa.hsi.s3

import cats.effect.Sync
import org.apache.hadoop.conf.Configuration

object S3Configuration {
  lazy val DEFAULT = {
    val conf = new Configuration()
    conf.set("fs.s3.impl", classOf[org.apache.hadoop.fs.s3a.S3AFileSystem].getName)
    conf.set("fs.s3a.aws.credentials.provider", classOf[com.amazonaws.auth.DefaultAWSCredentialsProviderChain].getName)
    conf.set("fs.s3a.endpoint", "s3.eu-west-2.amazonaws.com")
    conf
  }

  def defaultSync[F[_]: Sync]: F[Configuration] = Sync[F].delay(DEFAULT)
}
