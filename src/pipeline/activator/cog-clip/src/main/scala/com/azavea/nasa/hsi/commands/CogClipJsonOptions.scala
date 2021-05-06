package com.azavea.nasa.hsi.commands

import com.monovore.decline.Opts

trait CogClipJsonOptions {
  val clipCogConfigJson: Opts[CogClipConfig] = Opts.option[CogClipConfig](long = "pipeline", help = "JSON that sets application arguments.")
}
