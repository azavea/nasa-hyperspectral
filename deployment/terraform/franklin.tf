#
# Security Group Resources
#
resource "aws_security_group" "alb" {
  name   = "sgFranklinLoadBalancer"
  vpc_id = module.vpc.id

  tags = {
    Name    = "sgFranklinLoadBalancer",
    Project = var.project
  }
}

resource "aws_security_group" "franklin" {
  name   = "sgFranklinEcsService"
  vpc_id = module.vpc.id

  tags = {
    Name    = "sgFranklinEcsService",
    Project = var.project
  }
}

#
# ALB Resources
#
resource "aws_lb" "franklin" {
  name            = "albFranklin"
  security_groups = [aws_security_group.alb.id]
  subnets         = module.vpc.public_subnet_ids

  enable_http2 = true

  tags = {
    Name    = "albFranklin"
    Project = var.project
  }
}

resource "aws_lb_target_group" "franklin" {
  name = "tgFranklin"

  health_check {
    healthy_threshold   = 3
    interval            = 30
    matcher             = 200
    protocol            = "HTTP"
    timeout             = 3
    path                = "/open-api/spec.yaml"
    unhealthy_threshold = 2
  }

  port     = 80
  protocol = "HTTP"
  vpc_id   = module.vpc.id

  target_type = "ip"

  tags = {
    Name    = "tgFranklin"
    Project = var.project
  }
}

resource "aws_lb_listener" "franklin_redirect" {
  load_balancer_arn = aws_lb.franklin.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = 443
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "franklin" {
  load_balancer_arn = aws_lb.franklin.id
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = module.cert.arn

  default_action {
    target_group_arn = aws_lb_target_group.franklin.id
    type             = "forward"
  }
}

#
# ECS Resources
#
resource "aws_ecs_cluster" "franklin" {
  name = "ecsCluster"
}

resource "aws_ecs_task_definition" "franklin" {
  family                   = "franklin"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.franklin_cpu
  memory                   = var.franklin_memory

  task_role_arn      = aws_iam_role.ecs_task_role.arn
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = templatefile("${path.module}/task-definitions/franklin.json.tmpl", {
    image = "quay.io/azavea/franklin:${var.franklin_image_tag}"

    db_user     = var.rds_database_username
    db_password = var.rds_database_password
    db_host     = aws_route53_record.database.fqdn
    db_port     = module.database.port
    db_name     = "franklin"
    api_host    = aws_route53_record.franklin.name

    aws_region = var.aws_region
  })

  tags = {
    Name    = "franklin",
    Project = var.project
  }
}

resource "aws_ecs_service" "franklin" {
  name            = "franklin"
  cluster         = aws_ecs_cluster.franklin.name
  task_definition = aws_ecs_task_definition.franklin.arn

  desired_count                      = var.franklin_desired_count
  deployment_minimum_healthy_percent = var.franklin_deployment_min_percent
  deployment_maximum_percent         = var.franklin_deployment_max_percent

  launch_type      = "FARGATE"
  platform_version = var.fargate_platform_version

  network_configuration {
    security_groups = [aws_security_group.franklin.id]
    subnets         = module.vpc.private_subnet_ids
  }


  load_balancer {
    target_group_arn = aws_lb_target_group.franklin.arn
    container_name   = "franklin"
    container_port   = 9090
  }

  depends_on = [aws_lb_listener.franklin]
}

#
# CloudWatch Resources
#
resource "aws_cloudwatch_log_group" "franklin" {
  name              = "logFranklin"
  retention_in_days = 30
}
