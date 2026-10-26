import json
import pulumi
import pulumi_aws as aws

# -- Networking
vpc = aws.ec2.Vpc("watchdog-vpc", 
    cidr_block="10.0.0.0/16",  # noqa
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "watchdog-vpc"}
)

igw = aws.ec2.InternetGateway("watchdog-igw",
    vpc_id=vpc.id,
    tags={"Name": "watchdog-igw"})

subnet_a = aws.ec2.Subnet("watchdog-subnet-1a",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",  # noqa
    availability_zone="af-south-1a",
    map_public_ip_on_launch=True,
    tags={"Name": "watchdog-subnet-1a"})

subnet_b = aws.ec2.Subnet("watchdog-subnet-1b",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",  # noqa
    availability_zone="af-south-1b",
    map_public_ip_on_launch=True,
    tags={"Name": "watchdog-subnet-1b"})

subnet_c = aws.ec2.Subnet("watchdog-subnet-1c",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",  # noqa
    availability_zone="af-south-1c",
    map_public_ip_on_launch=True,
    tags={"Name": "watchdog-subnet-1c"})

route_table = aws.ec2.RouteTable("watchdog-public-rt",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": igw.id}],  # noqa
    tags={"Name": "watchdog-public-rt"})

for name, subnet in [("a", subnet_a), ("b", subnet_b), ("c", subnet_c)]:
    aws.ec2.RouteTableAssociation(f"watchdog-rta-{name}",
        subnet_id=subnet.id,
        route_table_id=route_table.id)

# --- Security groups
alb_sg = aws.ec2.SecurityGroup("watchdog-alb-sg",
    vpc_id=vpc.id,
    description="ALB - public HTTP/HTTPS",
    ingress=[
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "watchdog-alb-sg"})

ecs_sg = aws.ec2.SecurityGroup("watchdog-ecs-instance-sg",
    vpc_id=vpc.id,
    description="ECS instances - traffic from ALB only",
    ingress=[
        {"protocol": "tcp", "from_port": 0, "to_port": 65535, "security_groups": [alb_sg.id]},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "watchdog-ecs-sg"})

staging_ecs_sg = aws.ec2.SecurityGroup("watchdog-staging-ecs-sg",
    vpc_id=vpc.id,
    description="Staging ECS instances - backend from ALB only",
    ingress=[
        {"protocol": "tcp", "from_port": 8000, "to_port": 8000, "security_groups": [alb_sg.id]},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "watchdog-staging-ecs-sg"})

rds_sg = aws.ec2.SecurityGroup("watchdog-rds-sg",
    vpc_id=vpc.id,
    description="RDS - Postgres from ECS instances only",
    ingress=[
        {"protocol": "tcp", "from_port": 5432, "to_port": 5432, "security_groups": [ecs_sg.id, staging_ecs_sg.id]},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "watchdog-rds-sg"})

redis_sg = aws.ec2.SecurityGroup("watchdog-redis-sg",
    vpc_id=vpc.id,
    description="RDS - Postgres from ECS instances only",
    ingress=[
        {"protocol": "tcp", "from_port": 6379, "to_port": 6379, "security_groups": [ecs_sg.id]},
    ],
    egress=[{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}],
    tags={"Name": "watchdog-redis-sg"})

# --- ECR

ecr_repo = aws.ecr.Repository("watchdog-backend-repo",
    name="watchdog-backend",
    image_tag_mutability="IMMUTABLE",
    image_scanning_configuration={"scan_on_push": True},
    tags={"Name": "watchdog-backend"})

# --- Secrets Manager 
prod_secret = aws.secretsmanager.Secret("watchdog-prod-env",
    name="watchdog/prod/env",
    description="WatchDog production environment variables"
)

# --- Data tier : RDS and elasticache
db_subnet_group = aws.rds.SubnetGroup("watchdog-db-subnet-group",
    subnet_ids=[subnet_a.id, subnet_b.id],
    tags={"Name": "watchdog-db-subnet-group"})

redis_subnet_group = aws.elasticache.SubnetGroup("watchdog-redis-subnet-group",
    subnet_ids=[subnet_a.id, subnet_b.id])

db_instance = aws.rds.Instance("watchdog-db",
    identifier="watchdog-db",
    engine="postgres",
    engine_version="16",
    instance_class="db.t3.micro",
    allocated_storage=20,
    db_name="watchdog_production",
    username="watchdog",
    password=pulumi.Config().require_secret("db_password"),
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[rds_sg.id],
    publicly_accessible=False,
    skip_final_snapshot=True,
    multi_az=False,
    tags={"Name": "watchdog-db"})

redis_cluster = aws.elasticache.Cluster("watchdog-redis",
    cluster_id="watchdog-redis",
    engine="redis",
    node_type="cache.t4g.micro",
    num_cache_nodes=1,
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[redis_sg.id])

# --- GitHub Actions OIDC
REPO = "COS301-SE-2026/Neighbourhood-WatchDog"
ACCOUNT_ID = aws.get_caller_identity().account_id

github_oidc = aws.iam.OpenIdConnectProvider("github-oidc",
    url="https://token.actions.githubusercontent.com",
    client_id_lists=["sts.amazonaws.com"])

def github_trust(subjects: list[str]):
    return github_oidc.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Federated": arn},
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
                "StringLike": {"token.actions.githubusercontent.com:sub": subjects},
            },
        }],
    }))

# CI pushes images from pushes to dev/main (no GitHub environment on that job)
gha_ci_role = aws.iam.Role("gha-ci-role",
    name="watchdog-gha-ci",
    assume_role_policy=github_trust([
        f"repo:{REPO}:ref:refs/heads/dev",
        f"repo:{REPO}:ref:refs/heads/main",
    ]))

aws.iam.RolePolicy("gha-ci-ecr-push",
    role=gha_ci_role.id,
    policy=ecr_repo.arn.apply(lambda repo_arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": "ecr:GetAuthorizationToken", "Resource": "*"},
            {"Effect": "Allow", "Resource": repo_arn, "Action": [
                "ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage",
                "ecr:BatchGetImage", "ecr:DescribeImages",
            ]},
        ],
    })))

def deploy_policy(cluster_name: str):
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Resource": "*", "Action": [
                "ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition",
                "ecs:DescribeServices", "ecs:DescribeTasks",
                "ecr:GetAuthorizationToken", "ecr:DescribeImages", "ecr:BatchGetImage",
            ]},
            {"Effect": "Allow", "Resource": "*",
             "Action": ["ecs:UpdateService", "ecs:RunTask"],
             "Condition": {"ArnEquals": {"ecs:cluster": f"arn:aws:ecs:af-south-1:{ACCOUNT_ID}:cluster/{cluster_name}"}}},
            {"Effect": "Allow", "Action": "iam:PassRole",
             "Resource": f"arn:aws:iam::{ACCOUNT_ID}:role/watchdog-*",
             "Condition": {"StringEquals": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}}},
        ],
    })

gha_staging_role = aws.iam.Role("gha-staging-role",
    name="watchdog-gha-staging",
    assume_role_policy=github_trust([f"repo:{REPO}:environment:Staging"]))
aws.iam.RolePolicy("gha-staging-deploy", role=gha_staging_role.id,
    policy=deploy_policy("watchdog-staging-cluster"))

gha_prod_role = aws.iam.Role("gha-prod-role",
    name="watchdog-gha-prod",
    assume_role_policy=github_trust([f"repo:{REPO}:environment:Production"]))
aws.iam.RolePolicy("gha-prod-deploy", role=gha_prod_role.id,
    policy=deploy_policy("watchdog-prod-cluster"))


pulumi.export("vpc_id", vpc.id)
pulumi.export("subnet_ids", [subnet_a.id, subnet_b.id, subnet_c.id])
pulumi.export("alb_sg_id", alb_sg.id)
pulumi.export("ecs_sg_id", ecs_sg.id)
pulumi.export("staging_ecs_sg_id", staging_ecs_sg.id)
pulumi.export("ecr_repo_url", ecr_repo.repository_url)
pulumi.export("db_endpoint", db_instance.endpoint)
pulumi.export("redis_endpoint", redis_cluster.cache_nodes[0].address)
pulumi.export("rds_sg_id", rds_sg.id)
pulumi.export("gha_ci_role_arn", gha_ci_role.arn)
pulumi.export("gha_staging_role_arn", gha_staging_role.arn)
pulumi.export("gha_prod_role_arn", gha_prod_role.arn)
