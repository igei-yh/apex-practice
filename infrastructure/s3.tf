resource "aws_s3_bucket" "bucket" {
  bucket = "technoarc-tfstate"
  acl    = "private"

  tags {
    Name = "technoarc-tfstate"
  }
}
