provider "aws" {
  version = "~> 3.13.0"
  profile = var.profile
  region  = var.region
}

provider "template" {
  version = "~> 2.2.0"
}

provider "archive" {
  version = "~> 2.0.0"
}
