resource "terraform_data" "validate_subnet_lengths" {
  input = length(var.availability_zones)

  lifecycle {
    precondition {
      condition = (
        length(var.availability_zones) == length(var.public_subnet_cidrs) &&
        length(var.availability_zones) == length(var.private_app_subnet_cidrs) &&
        length(var.availability_zones) == length(var.private_db_subnet_cidrs)
      )

      error_message = "Each subnet CIDR list must contain exactly one CIDR per Availability Zone."
    }
  }
}