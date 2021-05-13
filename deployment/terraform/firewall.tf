#
# Bastion security group resources
#
resource "aws_security_group_rule" "bastion_ssh_ingress" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = [var.external_access_cidr_block]

  security_group_id = module.vpc.bastion_security_group_id
}

resource "aws_security_group_rule" "bastion_rds_egress" {
  type      = "egress"
  from_port = module.database.port
  to_port   = module.database.port
  protocol  = "tcp"

  security_group_id        = module.vpc.bastion_security_group_id
  source_security_group_id = module.database.database_security_group_id
}

resource "aws_security_group_rule" "bastion_http_egress" {
  type             = "egress"
  from_port        = 80
  to_port          = 80
  protocol         = "tcp"
  cidr_blocks      = ["0.0.0.0/0"]
  ipv6_cidr_blocks = ["::/0"]

  security_group_id = module.vpc.bastion_security_group_id
}

resource "aws_security_group_rule" "bastion_https_egress" {
  type             = "egress"
  from_port        = 443
  to_port          = 443
  protocol         = "tcp"
  cidr_blocks      = ["0.0.0.0/0"]
  ipv6_cidr_blocks = ["::/0"]

  security_group_id = module.vpc.bastion_security_group_id
}

#
# RDS security group resources
#
resource "aws_security_group_rule" "rds_bastion_ingress" {
  type      = "ingress"
  from_port = module.database.port
  to_port   = module.database.port
  protocol  = "tcp"

  security_group_id        = module.database.database_security_group_id
  source_security_group_id = module.vpc.bastion_security_group_id
}

resource "aws_security_group_rule" "rds_franklin_ingress" {
  type      = "ingress"
  from_port = module.database.port
  to_port   = module.database.port
  protocol  = "tcp"

  security_group_id        = module.database.database_security_group_id
  source_security_group_id = aws_security_group.franklin.id
}


#
# Franklin ALB security group resources
#
resource "aws_security_group_rule" "alb_http_ingress" {
  type             = "ingress"
  from_port        = 80
  to_port          = 80
  protocol         = "tcp"
  cidr_blocks      = ["0.0.0.0/0"]
  ipv6_cidr_blocks = ["::/0"]

  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "alb_https_ingress" {
  type             = "ingress"
  from_port        = 443
  to_port          = 443
  protocol         = "tcp"
  cidr_blocks      = ["0.0.0.0/0"]
  ipv6_cidr_blocks = ["::/0"]

  security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "alb_franklin_egress" {
  type      = "egress"
  from_port = 9090
  to_port   = 9090
  protocol  = "tcp"

  security_group_id        = aws_security_group.alb.id
  source_security_group_id = aws_security_group.franklin.id
}

#
# Franklin container instance security group resources
#
resource "aws_security_group_rule" "franklin_https_egress" {
  type             = "egress"
  from_port        = 443
  to_port          = 443
  protocol         = "tcp"
  cidr_blocks      = ["0.0.0.0/0"]
  ipv6_cidr_blocks = ["::/0"]

  security_group_id = aws_security_group.franklin.id
}

resource "aws_security_group_rule" "franklin_alb_ingress" {
  type      = "ingress"
  from_port = 9090
  to_port   = 9090
  protocol  = "tcp"

  security_group_id        = aws_security_group.franklin.id
  source_security_group_id = aws_security_group.alb.id
}

resource "aws_security_group_rule" "franklin_rds_egress" {
  type      = "egress"
  from_port = module.database.port
  to_port   = module.database.port
  protocol  = "tcp"

  security_group_id        = aws_security_group.franklin.id
  source_security_group_id = module.database.database_security_group_id
}

#
# Batch container instance security group resources
#
resource "aws_security_group_rule" "batch_http_egress" {
  type        = "egress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]

  security_group_id = aws_security_group.batch.id
}

resource "aws_security_group_rule" "batch_https_egress" {
  type        = "egress"
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]

  security_group_id = aws_security_group.batch.id
}

resource "aws_security_group_rule" "batch_bastion_ingress" {
  type      = "ingress"
  from_port = 22
  to_port   = 22
  protocol  = "tcp"

  security_group_id        = aws_security_group.batch.id
  source_security_group_id = module.vpc.bastion_security_group_id
}
