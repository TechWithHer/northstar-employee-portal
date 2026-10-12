check "subnet_list_lengths" {
  assert {
    condition = (
      length(var.availability_zones) == length(var.public_subnet_cidrs) &&
      length(var.availability_zones) == length(var.private_app_subnet_cidrs) &&
      length(var.availability_zones) == length(var.private_db_subnet_cidrs)
    )

    error_message = "Each subnet CIDR list must contain exactly one entry per Availability Zone."
  }
}