resource "aws_security_group" "worker_group_management" {
  name_prefix = "worker_group_management"
  vpc_id      = module.vpc.id

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [
      "10.0.0.0/8",
    ]
  }
}
