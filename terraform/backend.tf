terraform {
  backend "s3" {
    bucket       = "northstar-v2-tfstate"
    key          = "northstar/v2/networking/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }



}
