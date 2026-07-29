module "eks" {

  source = "terraform-aws-modules/eks/aws"

  version = "20.24.2"

  cluster_name = var.cluster_name

  cluster_version = var.cluster_version

  vpc_id = module.vpc.vpc_id

  subnet_ids = module.vpc.private_subnets

  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {

    student_nodes = {

      desired_size = 2

      min_size = 2

      max_size = 3

      instance_types = [
        "t3.medium"
      ]

      capacity_type = "ON_DEMAND"

    }

  }

  tags = {
    Environment = "Student"
    Terraform = "true"
  }

}