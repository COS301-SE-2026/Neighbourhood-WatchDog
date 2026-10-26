import base64
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
prod = pulumi.StackReference(config.require("prodStack"))
image_tag = config.require("imageTag")
# set to true once the ACM certificate shows ISSUED
api_cert_issued = config.get_bool("apiCertIssued") or False

PREFIX = "watchdog-staging"
REGION = "af-south-1"
API_DOMAIN = "api-staging.neighbourhoodwatchdog.co.za"

REDIS_IMAGE = "redis@sha256:858f009f9709ce576febc734aa78b8f6d624b82571f9ddb6bda4377c833b3499"

ALL_EGRESS = [{"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}] #noqa

vpc_id = prod.get_output("vpc_id")
subnet_ids = prod.get_output("subnet_ids")
ecs_sg_id = prod.get_output("staging_ecs_sg_id")
ecr_repo_url = prod.get_output("ecr_repo_url")

alb = aws.lb.get_load_balancer(name="watchdog-load-balancer")
https_listener = aws.lb.get_listener(load_balancer_arn=alb.arn, port=443)
http_listener = aws.lb.get_listener(load_balancer_arn=alb.arn, port=80)

def assume_role(service: str) -> str:
    return json.dumps({"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": {"Service": service}, "Action": "sts:AssumeRole"}]})


# --- Storage, secrets and logs
clips_bucket = aws.s3.Bucket(f"{PREFIX}-clips",
    bucket="watchdog-staging-clips",
    force_destroy=True)

aws.s3.BucketPublicAccessBlock(f"{PREFIX}-clips-public-block",
    bucket=clips_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True)

aws.s3.BucketLifecycleConfiguration(f"{PREFIX}-clips-expiry",
    bucket=clips_bucket.id,
    rules=[{"id": "expire-staging-clips", "status": "Enabled", "filter": {}, "expiration": {"days": 14}}])

env_secret = aws.secretsmanager.Secret(f"{PREFIX}-env",
    name="watchdog/staging/env",
    description="WatchDog staging environment variables",
    recovery_window_in_days=0)

log_group = aws.cloudwatch.LogGroup(f"{PREFIX}-logs",
    name="/ecs/watchdog-staging",
    retention_in_days=7)

# --- IAM (names start with watchdog- so the GitHub deploy role can pass them)
execution_role = aws.iam.Role(f"{PREFIX}-execution-role",
    name=f"{PREFIX}-ecs-execution-role",
    assume_role_policy=assume_role("ecs-tasks.amazonaws.com"))

aws.iam.RolePolicyAttachment(f"{PREFIX}-execution-managed",
    role=execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy")

aws.iam.RolePolicy(f"{PREFIX}-execution-secret",
    role=execution_role.id,
    policy=env_secret.arn.apply(lambda arn: json.dumps({"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": arn}]})))

task_role = aws.iam.Role(f"{PREFIX}-task-role",
    name=f"{PREFIX}-task-role",
    assume_role_policy=assume_role("ecs-tasks.amazonaws.com"))

aws.iam.RolePolicy(f"{PREFIX}-task-s3",
    role=task_role.id,
    policy=clips_bucket.arn.apply(lambda arn: json.dumps({"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow",
        "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
        "Resource": [arn, f"{arn}/*"]}]})))

instance_role = aws.iam.Role(f"{PREFIX}-instance-role",
    name=f"{PREFIX}-ecs-instance-role",
    assume_role_policy=assume_role("ec2.amazonaws.com"))

for name, policy_arn in {
    "ecs": "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role",
    "ssm": "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
}.items():
    aws.iam.RolePolicyAttachment(f"{PREFIX}-instance-{name}", role=instance_role.name, policy_arn=policy_arn)

instance_profile = aws.iam.InstanceProfile(f"{PREFIX}-instance-profile",
    name=f"{PREFIX}-ecs-instance-profile",
    role=instance_role.name)

# --- ECS host: one t3.small, no capacity provider so nothing rescales it behind our back
cluster = aws.ecs.Cluster(f"{PREFIX}-cluster", name=f"{PREFIX}-cluster")

ecs_ami = aws.ssm.get_parameter(
    name="/aws/service/ecs/optimized-ami/amazon-linux-2023/recommended/image_id").value

launch_template = aws.ec2.LaunchTemplate(f"{PREFIX}-launch-template",
    name=f"{PREFIX}-launch-template",
    image_id=ecs_ami,
    instance_type="t3.small",
    iam_instance_profile={"arn": instance_profile.arn},
    vpc_security_group_ids=[ecs_sg_id],
    user_data=base64.b64encode(
        f"#!/bin/bash\necho ECS_CLUSTER={PREFIX}-cluster >> /etc/ecs/ecs.config\n".encode()).decode(),
    metadata_options={"http_tokens": "required", "http_put_response_hop_limit": 2},
    opts=pulumi.ResourceOptions(ignore_changes=["image_id"]))

aws.autoscaling.Group(f"{PREFIX}-asg",
    name=f"{PREFIX}-asg",
    min_size=0,
    max_size=1,
    desired_capacity=1,
    vpc_zone_identifiers=subnet_ids,
    launch_template={"id": launch_template.id, "version": "$Latest"},
    tags=[{"key": "Name", "value": f"{PREFIX}-ecs", "propagate_at_launch": True}],
    opts=pulumi.ResourceOptions(ignore_changes=["desired_capacity"]))

# --- Task definition: backend, worker, beat and Redis in one task on one host
SECRET_KEYS = [
    "SECRET_KEY", "DATABASE_URL", "REDIS_URL", "S3_BUCKET_NAME",
    "COGNITO_USER_POOL_ID", "COGNITO_CLIENT_ID", "COGNITO_REGION",
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "NOTIFICATION_ENABLED",
    "RTSP_ENCRYPTION_KEY", "MEDIAMTX_PUBLISH_MASTER_KEY", "FRONTEND_URL",
    "SMTP_SENDER_EMAIL", "SMTP_APP_PASSWORD",
    "REFRESH_COOKIE_SAMESITE", "REFRESH_COOKIE_MAX_AGE", "FIREBASE_CREDENTIALS_JSON",
]

ENVIRONMENT = {
    "APP_ENV": "staging",
    "DEBUG": "false",
    "TESTING": "false",
    "AWS_REGION": REGION,
    "REFRESH_COOKIE_SECURE": "true",
    "WEAPON_INCIDENT_WINDOW_SECONDS": "30",
}


def logs(log_group_name: str, prefix: str) -> dict:
    return {"logDriver": "awslogs", "options": {
        "awslogs-group": log_group_name,
        "awslogs-region": REGION,
        "awslogs-stream-prefix": prefix
    }}


def container_definitions(image: str, secret_arn: str, log_group_name: str) -> str:
    app = {
        "image": image,
        "essential": True,
        "links": ["redis"],
        "dependsOn": [{"containerName": "redis", "condition": "START"}],
        "environment": [{"name": k, "value": v} for k, v in ENVIRONMENT.items()],
        "secrets": [{"name": k, "valueFrom": f"{secret_arn}:{k}::"} for k in SECRET_KEYS],
    }

    return json.dumps([
        {
            "name": "redis",
            "image": REDIS_IMAGE,
            "essential": True,
            "memoryReservation": 64,
            "entryPoint": ["sh", "-c"],
            "command": ['exec docker-entrypoint.sh redis-server --requirepass "$REDIS_PASSWORD" --save ""'],
            "secrets": [{"name": "REDIS_PASSWORD", "valueFrom": f"{secret_arn}:REDIS_PASSWORD::"}],
            "logConfiguration": logs(log_group_name, "redis"),
        },
        {
            **app,
            "name": "backend",
            "memoryReservation": 512,
            "portMappings": [{"containerPort": 8000, "hostPort": 8000, "protocol": "tcp"}],
            "logConfiguration": logs(log_group_name, "backend"),
        },
        {
            **app,
            "name": "worker",
            "memoryReservation": 384,
            "command": ["celery", "-A", "app.core.celery_app", "worker",
                        "--loglevel=info", "--pool=threads", "--concurrency=2"],
            "logConfiguration": logs(log_group_name, "worker"),
        },
        {
            **app,
            "name": "beat",
            "memoryReservation": 128,
            "command": ["celery", "-A", "app.core.celery_app", "beat", "--loglevel=info"],
            "logConfiguration": logs(log_group_name, "beat"),
        },
    ])


def migrate_container_definitions(image: str, secret_arn: str, log_group_name: str) -> str:
    return json.dumps([{
        "name": "migrate",
        "image": image,
        "essential": True,
        "memoryReservation": 256,
        "command": ["alembic", "upgrade", "head"],
        "environment": [{"name": k, "value": v} for k, v in ENVIRONMENT.items()],
        "secrets": [{"name": k, "valueFrom": f"{secret_arn}:{k}::"} for k in SECRET_KEYS],
        "logConfiguration": logs(log_group_name, "migrate"),
    }])


task_definition = aws.ecs.TaskDefinition(f"{PREFIX}-task",
    family=f"{PREFIX}-task",
    network_mode="bridge",
    requires_compatibilities=["EC2"],
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(ecr_repo_url, env_secret.arn, log_group.name).apply(
        lambda args: container_definitions(f"{args[0]}:{image_tag}", args[1], args[2])))

# One-off tasks (migrations, seeding), there's no port so it can run beside the service on one host
migrate_task_definition = aws.ecs.TaskDefinition(f"{PREFIX}-migrate",
    family=f"{PREFIX}-migrate",
    network_mode="bridge",
    requires_compatibilities=["EC2"],
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(ecr_repo_url, env_secret.arn, log_group.name).apply(
        lambda args: migrate_container_definitions(f"{args[0]}:{image_tag}", args[1], args[2])))

# --- Load balancing: host rule for api-staging on the shared ALB
target_group = aws.lb.TargetGroup(f"{PREFIX}-tg",
    name=f"{PREFIX}-tg",
    port=8000,
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc_id,
    deregistration_delay=10,
    health_check={"path": "/health", "matcher": "200", "interval": 15, "healthy_threshold": 2})

api_cert = aws.acm.Certificate(f"{PREFIX}-api-cert",
    domain_name=API_DOMAIN,
    validation_method="DNS")

if api_cert_issued:
    aws.lb.ListenerCertificate(f"{PREFIX}-api-listener-cert",
        listener_arn=https_listener.arn,
        certificate_arn=api_cert.arn)

    https_rule = aws.lb.ListenerRule(f"{PREFIX}-https-rule",
        listener_arn=https_listener.arn,
        priority=10,
        conditions=[{"host_header": {"values": [API_DOMAIN]}}],
        actions=[{"type": "forward", "target_group_arn": target_group.arn}])

    aws.lb.ListenerRule(f"{PREFIX}-http-redirect",
        listener_arn=http_listener.arn,
        priority=10,
        conditions=[{"host_header": {"values": [API_DOMAIN]}}],
        actions=[{"type": "redirect", "redirect": {
            "protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}}])

    # CI owns the task definition revision after the first deploy
    aws.ecs.Service(f"{PREFIX}-service",
        name=f"{PREFIX}-service",
        cluster=cluster.arn,
        task_definition=task_definition.arn,
        desired_count=1,
        launch_type="EC2",
        deployment_minimum_healthy_percent=0,
        deployment_maximum_percent=100,
        health_check_grace_period_seconds=120,
        load_balancers=[{"target_group_arn": target_group.arn, "container_name": "backend", "container_port": 8000}],
        opts=pulumi.ResourceOptions(depends_on=[https_rule], ignore_changes=["task_definition", "desired_count"]))

# --- MediaMTX: separate host, its auth hook points at api-staging
mediamtx_sg = aws.ec2.SecurityGroup(f"{PREFIX}-mediamtx-sg",
    vpc_id=vpc_id,
    description="Staging MediaMTX - RTSP, WebRTC and ACME only",
    ingress=[
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"], "description": "certbot HTTP-01"},
        {"protocol": "tcp", "from_port": 8554, "to_port": 8554, "cidr_blocks": ["0.0.0.0/0"], "description": "RTSP publish"},
        {"protocol": "tcp", "from_port": 8889, "to_port": 8889, "cidr_blocks": ["0.0.0.0/0"], "description": "WebRTC signalling"},
        {"protocol": "udp", "from_port": 8189, "to_port": 8189, "cidr_blocks": ["0.0.0.0/0"], "description": "WebRTC media"},
    ],
    egress=ALL_EGRESS,
    tags={"Name": f"{PREFIX}-mediamtx-sg"})

mediamtx_role = aws.iam.Role(f"{PREFIX}-mediamtx-role",
    name=f"{PREFIX}-mediamtx-role",
    assume_role_policy=assume_role("ec2.amazonaws.com"))

aws.iam.RolePolicyAttachment(f"{PREFIX}-mediamtx-ssm",
    role=mediamtx_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")

mediamtx_profile = aws.iam.InstanceProfile(f"{PREFIX}-mediamtx-profile",
    name=f"{PREFIX}-mediamtx-profile",
    role=mediamtx_role.name)

ubuntu_arm_ami = aws.ssm.get_parameter(
    name="/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id").value

MEDIAMTX_USER_DATA = """#!/bin/bash
set -eux
apt-get update
apt-get install -y docker.io docker-compose-v2 certbot
usermod -aG docker ubuntu
mkdir -p /home/ubuntu/app /opt/mediamtx-certs
chown ubuntu:ubuntu /home/ubuntu/app
"""

mediamtx = aws.ec2.Instance(f"{PREFIX}-mediamtx",
    ami=ubuntu_arm_ami,
    instance_type="t4g.micro",
    subnet_id=subnet_ids.apply(lambda ids: ids[0]),
    vpc_security_group_ids=[mediamtx_sg.id],
    iam_instance_profile=mediamtx_profile.name,
    user_data=MEDIAMTX_USER_DATA,
    root_block_device={"volume_size": 8, "volume_type": "gp3"},
    metadata_options={"http_tokens": "required"},
    tags={"Name": f"{PREFIX}-mediamtx"},
    opts=pulumi.ResourceOptions(ignore_changes=["ami", "user_data"]))

mediamtx_eip = aws.ec2.Eip(f"{PREFIX}-mediamtx-eip",
    domain="vpc",
    instance=mediamtx.id,
    tags={"Name": f"{PREFIX}-mediamtx-eip"})

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("api_cert_validation", api_cert.domain_validation_options.apply(
    lambda options: [{"name": o.resource_record_name, "type": o.resource_record_type, "value": o.resource_record_value}
                     for o in options]))
pulumi.export("mediamtx_public_ip", mediamtx_eip.public_ip)
pulumi.export("mediamtx_instance_id", mediamtx.id)
pulumi.export("cluster_name", cluster.name)
pulumi.export("service_name", f"{PREFIX}-service")
pulumi.export("task_family", task_definition.family)
pulumi.export("env_secret_arn", env_secret.arn)
pulumi.export("clips_bucket", clips_bucket.bucket)
pulumi.export("migrate_family", migrate_task_definition.family)