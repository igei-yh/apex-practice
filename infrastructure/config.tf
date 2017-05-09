provider "aws" {
  region = "ap-northeast-1"
}

provider "aws" {
  region = "us-east-1"
  alias  = "virginia"
}

terraform {
  backend "s3" {
    bucket = "technoarc-tfstate"
    key    = "technoarc/terraform.tfstate"
    region = "ap-northeast-1"
  }
}
