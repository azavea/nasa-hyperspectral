name := "cog-clip"
organization := "NASA Hyperspectral"
version := "0.1.0"

scalaVersion := "2.12.12"

libraryDependencies ++= Seq(
  "com.azavea.stac4s" %% "core" % "0.0.19",
  "com.monovore" %% "decline" % "1.3.0",
  "com.monovore" %% "decline-effect" % "1.3.0",
  "com.monovore" %% "decline-refined" % "1.3.0",
  "org.locationtech.geotrellis" %% "geotrellis-raster" % "3.5.1",
  "org.locationtech.geotrellis" %% "geotrellis-vector" % "3.5.1",
  "org.typelevel" %% "cats-effect" % "2.3.1",
  "software.amazon.awssdk" % "s3" % "2.15.50"
)

initialCommands in console :=
"""
import geotrellis.vector._
import geotrellis.raster._
""".stripMargin
