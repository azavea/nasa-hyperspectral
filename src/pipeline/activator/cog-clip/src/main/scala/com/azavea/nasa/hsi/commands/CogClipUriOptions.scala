package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts

import java.net.URI

trait CogClipUriOptions {
  val clipCogConfigUri: Opts[URI] = Opts.option[URI](long = "uri", help = "JSON that sets application arguments.")
}
