name := "cog-clip"
organization := "com.azavea"
version := "0.1.0"

scalaVersion := "2.12.12"

addCompilerPlugin("org.typelevel" %% "kind-projector"     % "0.11.2" cross CrossVersion.full)
addCompilerPlugin("com.olegpy"    %% "better-monadic-for" % "0.3.1")

resolvers ++= Seq(
  "eclipse-releases" at "https://repo.eclipse.org/content/groups/releases",
  "eclipse-snapshots" at "https://repo.eclipse.org/content/groups/snapshots"
)

libraryDependencies ++= Seq(
  "org.locationtech.geotrellis"   %% "geotrellis-s3"                  % "3.5.2-SNAPSHOT",
  "org.locationtech.geotrellis"   %% "geotrellis-gdal"                % "3.5.2-SNAPSHOT",
  "com.azavea.stac4s"             %% "client"                         % "0.0.21",
  "com.monovore"                  %% "decline"                        % "1.3.0",
  "com.monovore"                  %% "decline-effect"                 % "1.3.0",
  "com.monovore"                  %% "decline-refined"                % "1.3.0",
  "io.circe"                      %% "circe-refined"                  % "0.13.0",
  "org.typelevel"                 %% "cats-effect"                    % "2.3.1",
  "io.chrisdavenport"             %% "log4cats-slf4j"                 % "1.1.1",
  "com.softwaremill.sttp.client3" %% "async-http-client-backend-cats" % "3.0.0-RC15",
  "ch.qos.logback"                 % "logback-classic"                % "1.2.3",
  "org.scalatest"                 %% "scalatest"                      % "3.2.3" % Test
)

assembly / assemblyJarName := "cog-clip-assembly.jar"

assembly / test := {}

assembly / assemblyMergeStrategy := {
  case "reference.conf"   => MergeStrategy.concat
  case "application.conf" => MergeStrategy.concat
  case PathList("META-INF", xs @ _*) =>
    xs match {
      case ("MANIFEST.MF" :: Nil) => MergeStrategy.discard
      // Concatenate everything in the services directory to keep GeoTools happy.
      case ("services" :: _ :: Nil) =>
        MergeStrategy.concat
      // Concatenate these to keep JAI happy.
      case ("javax.media.jai.registryFile.jai" :: Nil) | ("registryFile.jai" :: Nil) | ("registryFile.jaiext" :: Nil) =>
        MergeStrategy.concat
      case (name :: Nil) =>
        // Must exclude META-INF/*.([RD]SA|SF) to avoid "Invalid signature file digest for Manifest main attributes" exception.
        if (name.endsWith(".RSA") || name.endsWith(".DSA") || name.endsWith(".SF"))
          MergeStrategy.discard
        else
          MergeStrategy.first
      case _ => MergeStrategy.first
    }
  case _ => MergeStrategy.first
}
