name := "cog-clip"
organization := "com.azavea"
version := "0.1.0"

scalaVersion := "2.13.6"
crossScalaVersions := Seq("2.12.14", "2.13.6")

scalacOptions ++= Seq(
  "-deprecation",
  "-unchecked",
  "-feature",
  "-language:implicitConversions",
  "-language:reflectiveCalls",
  "-language:higherKinds",
  "-language:postfixOps",
  "-language:existentials",
  "-language:experimental.macros",
  "-feature",
  // "-Yrangepos",            // required by SemanticDB compiler plugin
  // "-Ywarn-unused-import",  // required by `RemoveUnused` rule
  "-target:jvm-1.8"
)

scalacOptions ++= (CrossVersion.partialVersion(scalaVersion.value) match {
  case Some((2, 13)) => Seq("-Ymacro-annotations")   // replaces paradise in 2.13
  case Some((2, 12)) => Seq("-Ypartial-unification") // required by Cats
  case _             => Nil
})

resolvers ++= Seq(
  "eclipse-releases" at "https://repo.eclipse.org/content/groups/releases",
  "eclipse-snapshots" at "https://repo.eclipse.org/content/groups/snapshots",
  "oss-snapshots" at "https://oss.sonatype.org/content/repositories/snapshots",
  "jitpack" at "https://jitpack.io"
)

addCompilerPlugin("org.typelevel" %% "kind-projector"     % "0.13.0" cross CrossVersion.full)
addCompilerPlugin("com.olegpy"    %% "better-monadic-for" % "0.3.1")

libraryDependencies ++= (CrossVersion.partialVersion(scalaVersion.value) match {
  case Some((2, 12)) => Seq(compilerPlugin("org.scalamacros" % "paradise" % "2.1.1" cross CrossVersion.full))
  case _             => Nil
})

def ver(for212: String, for213: String) = Def.setting {
  CrossVersion.partialVersion(scalaVersion.value) match {
    case Some((2, 12)) => for212
    case Some((2, 13)) => for213
    case _             => sys.error("not good")
  }
}

val declineVersion    = "1.4.0"
val geotrellisVersion = Def.setting(ver("3.6.0", "3.6.1-SNAPSHOT").value)
val stac4sVersion     = Def.setting(ver("0.5.0-13-g35ad8d4-SNAPSHOT", "0.5.0-13-g35ad8d4-SNAPSHOT").value)

libraryDependencies ++= Seq(
  "org.locationtech.geotrellis"   %% "geotrellis-s3"                      % geotrellisVersion.value,
  "org.locationtech.geotrellis"   %% "geotrellis-gdal"                    % geotrellisVersion.value,
  "com.azavea.stac4s"             %% "client"                             % stac4sVersion.value,
  "com.monovore"                  %% "decline"                            % declineVersion,
  "com.monovore"                  %% "decline-effect"                     % declineVersion,
  "com.monovore"                  %% "decline-refined"                    % declineVersion,
  "io.circe"                      %% "circe-refined"                      % "0.14.1",
  "org.typelevel"                 %% "cats-effect"                        % "2.5.1",
  "io.chrisdavenport"             %% "log4cats-slf4j"                     % "1.1.1",
  "com.softwaremill.sttp.client3" %% "async-http-client-backend-cats-ce2" % "3.3.6",
  "ch.qos.logback"                 % "logback-classic"                    % "1.2.3",
  "tf.tofu"                       %% "tofu-core"                          % "0.10.2",
  "com.github.julien-truffaut"    %% "monocle-macro"                      % "2.1.0",
  "org.scalatest"                 %% "scalatest"                          % "3.2.9" % Test
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
