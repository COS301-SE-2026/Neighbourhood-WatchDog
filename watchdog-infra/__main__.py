import pulumi
import pulumi_aws as aws

watchdog_redis = aws.elasticache.Cluster("watchdog_redis",
    availability_zone="af-south-1b",
    az_mode="single-az",
    cluster_id="watchdog-redis",
    engine="redis",
    engine_version="7.1",
    ip_discovery="ipv4",
    maintenance_window="fri:02:00-fri:03:00",
    network_type="ipv4",
    node_type="cache.t4g.micro",
    num_cache_nodes=1,
    parameter_group_name="default.redis7",
    port=6379,
    region="af-south-1",
    security_group_ids=["sg-07979bd755370c2b2"],
    snapshot_window="23:30-00:30",
    subnet_group_name="watchdog-redis-subnet-group",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_cluster = aws.ecs.Cluster("watchdog_cluster",
    configuration={
        "execute_command_configuration": {
            "logging": "DEFAULT",
        },
    },
    name="watchdog-prod-cluster",
    region="af-south-1",
    settings=[{
        "name": "containerInsights",
        "value": "disabled",
    }],
    opts = pulumi.ResourceOptions(protect=True))

watchdog_backend_service = aws.ecs.Service("watchdog_backend_service",
    availability_zone_rebalancing="DISABLED",
    cluster="arn:aws:ecs:af-south-1:809809510183:cluster/watchdog-prod-cluster",
    deployment_circuit_breaker={
        "enable": True,
        "rollback": True,
    },
    deployment_configuration={
        "bake_time_in_minutes": "0",
        "strategy": "ROLLING",
    },
    deployment_controller={
        "type": "ECS",
    },
    desired_count=1,
    health_check_grace_period_seconds=60,
    iam_role="/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
    launch_type="EC2",
    load_balancers=[{
        "container_name": "backend",
        "container_port": 8000,
        "target_group_arn": "arn:aws:elasticloadbalancing:af-south-1:809809510183:targetgroup/watchdog-target-group/f1fcc819f6e19b5b",
    }],
    name="watchdog-backend-service",
    propagate_tags="NONE",
    region="af-south-1",
    scheduling_strategy="REPLICA",
    task_definition="watchdog-backend-task:33",
    wait_for_steady_state=False,
    opts = pulumi.ResourceOptions(protect=True))

watchdog_vpc = aws.ec2.Vpc("watchdog_vpc",
    cidr_block="172.31.0.0/16",
    enable_dns_hostnames=True,
    instance_tenancy="default",
    region="af-south-1",
    opts = pulumi.ResourceOptions(protect=True))

subnet_1a = aws.ec2.Subnet("subnet_1a",
    availability_zone="af-south-1a",
    cidr_block="172.31.0.0/20",
    map_public_ip_on_launch=True,
    private_dns_hostname_type_on_launch="ip-name",
    region="af-south-1",
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

subnet_1b = aws.ec2.Subnet("subnet_1b",
    availability_zone="af-south-1b",
    cidr_block="172.31.48.128/25",
    private_dns_hostname_type_on_launch="ip-name",
    region="af-south-1",
    tags={
        "Name": "RDS-Pvt-subnet-2",
    },
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

subnet_1c = aws.ec2.Subnet("subnet_1c",
    availability_zone="af-south-1c",
    cidr_block="172.31.49.0/25",
    private_dns_hostname_type_on_launch="ip-name",
    region="af-south-1",
    tags={
        "Name": "RDS-Pvt-subnet-3",
    },
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_redis_sg = aws.ec2.SecurityGroup("watchdog_redis_sg",
    description="Allow backend/celery access to ElastiCache Redis",
    egress=[{
        "cidr_blocks": ["0.0.0.0/0"],
        "from_port": 0,
        "protocol": "-1",
        "to_port": 0,
    }],
    ingress=[{
        "from_port": 6379,
        "protocol": "tcp",
        "security_groups": ["sg-002cf8f60b17dd248"],
        "to_port": 6379,
    }],
    name="watchdog-redis-sg",
    region="af-south-1",
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_ecs_sg = aws.ec2.SecurityGroup("watchdog_ecs_sg",
    description="Watchdog ECS instance security group",
    egress=[
        {
            "cidr_blocks": ["0.0.0.0/0"],
            "from_port": 0,
            "protocol": "-1",
            "to_port": 0,
        },
        {
            "cidr_blocks": ["0.0.0.0/0"],
            "from_port": 22,
            "protocol": "tcp",
            "to_port": 22,
        },
    ],
    ingress=[
        {
            "cidr_blocks": ["0.0.0.0/0"],
            "from_port": 22,
            "protocol": "tcp",
            "to_port": 22,
        },
        {
            "from_port": 32768,
            "protocol": "tcp",
            "security_groups": ["sg-0eb015bd6dce953e1"],
            "to_port": 65535,
        },
    ],
    name="watchdog-ecs-instance-sg",
    region="af-south-1",
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_worker_service = aws.ecs.Service("watchdog_worker_service",
    availability_zone_rebalancing="ENABLED",
    cluster="arn:aws:ecs:af-south-1:809809510183:cluster/watchdog-prod-cluster",
    deployment_circuit_breaker={
        "enable": False,
        "rollback": False,
    },
    deployment_configuration={
        "bake_time_in_minutes": "0",
        "strategy": "ROLLING",
    },
    deployment_controller={
        "type": "ECS",
    },
    deployment_minimum_healthy_percent=0,
    desired_count=1,
    launch_type="EC2",
    name="watchdog-celery-worker-service",
    propagate_tags="NONE",
    region="af-south-1",
    scheduling_strategy="REPLICA",
    task_definition="watchdog-celery-worker-task:18",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_beat_service = aws.ecs.Service("watchdog_beat_service",
    availability_zone_rebalancing="ENABLED",
    cluster="arn:aws:ecs:af-south-1:809809510183:cluster/watchdog-prod-cluster",
    deployment_circuit_breaker={
        "enable": False,
        "rollback": False,
    },
    deployment_configuration={
        "bake_time_in_minutes": "0",
        "strategy": "ROLLING",
    },
    deployment_controller={
        "type": "ECS",
    },
    deployment_minimum_healthy_percent=0,
    desired_count=1,
    launch_type="EC2",
    name="watchdog-celery-beat-service",
    propagate_tags="NONE",
    region="af-south-1",
    scheduling_strategy="REPLICA",
    task_definition="watchdog-celery-beat-task:20",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_redis_service = aws.ecs.Service("watchdog_redis_service",
    availability_zone_rebalancing="ENABLED",
    cluster="arn:aws:ecs:af-south-1:809809510183:cluster/watchdog-prod-cluster",
    deployment_circuit_breaker={
        "enable": False,
        "rollback": False,
    },
    deployment_configuration={
        "bake_time_in_minutes": "0",
        "strategy": "ROLLING",
    },
    deployment_controller={
        "type": "ECS",
    },
    launch_type="EC2",
    name="watchdog-redis-service",
    propagate_tags="NONE",
    region="af-south-1",
    scheduling_strategy="REPLICA",
    task_definition="watchdog-redis-task:2",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_backend_task = aws.ecs.TaskDefinition("watchdog_backend_task",
    container_definitions="[{\"environment\":[],\"essential\":true,\"image\":\"809809510183.dkr.ecr.af-south-1.amazonaws.com/watchdog-backend:6a8ef4e3126ddd47db510830513a7e4adfe02d0f\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-stream-prefix\":\"backend\",\"awslogs-group\":\"/ecs/watchdog-backend\",\"awslogs-create-group\":\"true\",\"awslogs-region\":\"af-south-1\"}},\"memoryReservation\":256,\"mountPoints\":[],\"name\":\"backend\",\"portMappings\":[{\"containerPort\":8000,\"hostPort\":0,\"protocol\":\"tcp\"}],\"secrets\":[{\"name\":\"AWS_REGION\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:AWS_REGION::\"},{\"name\":\"COGNITO_CLIENT_ID\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:COGNITO_CLIENT_ID::\"},{\"name\":\"COGNITO_REGION\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:COGNITO_REGION::\"},{\"name\":\"COGNITO_USER_POOL_ID\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:COGNITO_USER_POOL_ID::\"},{\"name\":\"DATABASE_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:DATABASE_URL::\"},{\"name\":\"DETECTION_CONFIDENCE_THRESHOLD\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:DETECTION_CONFIDENCE_THRESHOLD::\"},{\"name\":\"FAILOVER_CONTROLLER_TOKEN\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:FAILOVER_CONTROLLER_TOKEN::\"},{\"name\":\"FRONTEND_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:FRONTEND_URL::\"},{\"name\":\"GO2RTC_API_PASSWORD\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:GO2RTC_API_PASSWORD::\"},{\"name\":\"GO2RTC_API_USERNAME\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:GO2RTC_API_USERNAME::\"},{\"name\":\"MEDIAMTX_PUBLISH_MASTER_KEY\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:MEDIAMTX_PUBLISH_MASTER_KEY::\"},{\"name\":\"NOTIFICATION_ENABLED\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:NOTIFICATION_ENABLED::\"},{\"name\":\"POSTGRES_DB\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:POSTGRES_DB::\"},{\"name\":\"POSTGRES_PASSWORD\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:POSTGRES_PASSWORD::\"},{\"name\":\"POSTGRES_USER\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:POSTGRES_USER::\"},{\"name\":\"REDIS_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:REDIS_URL::\"},{\"name\":\"RTSP_ENCRYPTION_KEY\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:RTSP_ENCRYPTION_KEY::\"},{\"name\":\"S3_BUCKET_NAME\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:S3_BUCKET_NAME::\"},{\"name\":\"SECRET_KEY\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:SECRET_KEY::\"},{\"name\":\"TWILIO_ACCOUNT_SID\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:TWILIO_ACCOUNT_SID::\"},{\"name\":\"TWILIO_AUTH_TOKEN\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:TWILIO_AUTH_TOKEN::\"},{\"name\":\"TWILIO_WHATSAPP_FROM\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:TWILIO_WHATSAPP_FROM::\"}],\"systemControls\":[],\"volumesFrom\":[]}]",
    cpu="512",
    execution_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-execution-role",
    family="watchdog-backend-task",
    memory="512",
    network_mode="bridge",
    region="af-south-1",
    requires_compatibilities=["EC2"],
    task_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-role",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_worker_task = aws.ecs.TaskDefinition("watchdog_worker_task",
    container_definitions="[{\"command\":[\"celery\",\"-A\",\"app.core.celery_app\",\"worker\",\"--loglevel=info\"],\"environment\":[],\"essential\":true,\"image\":\"809809510183.dkr.ecr.af-south-1.amazonaws.com/watchdog-backend:6a8ef4e3126ddd47db510830513a7e4adfe02d0f\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-stream-prefix\":\"worker\",\"awslogs-group\":\"/ecs/watchdog-celery-worker\",\"awslogs-create-group\":\"true\",\"awslogs-region\":\"af-south-1\"}},\"memoryReservation\":256,\"mountPoints\":[],\"name\":\"celery-worker\",\"portMappings\":[],\"secrets\":[{\"name\":\"AWS_REGION\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:AWS_REGION::\"},{\"name\":\"DATABASE_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:DATABASE_URL::\"},{\"name\":\"REDIS_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:REDIS_URL::\"},{\"name\":\"S3_BUCKET_NAME\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:S3_BUCKET_NAME::\"}],\"systemControls\":[],\"volumesFrom\":[]}]",
    cpu="256",
    execution_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-execution-role",
    family="watchdog-celery-worker-task",
    memory="384",
    network_mode="bridge",
    region="af-south-1",
    requires_compatibilities=["EC2"],
    task_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-role",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_beat_task = aws.ecs.TaskDefinition("watchdog_beat_task",
    container_definitions="[{\"command\":[\"celery\",\"-A\",\"app.core.celery_app\",\"beat\",\"--loglevel=info\"],\"environment\":[],\"essential\":true,\"image\":\"809809510183.dkr.ecr.af-south-1.amazonaws.com/watchdog-backend:6a8ef4e3126ddd47db510830513a7e4adfe02d0f\",\"logConfiguration\":{\"logDriver\":\"awslogs\",\"options\":{\"awslogs-group\":\"/ecs/watchdog-celery-beat\",\"awslogs-create-group\":\"true\",\"awslogs-region\":\"af-south-1\",\"awslogs-stream-prefix\":\"beat\"}},\"memoryReservation\":96,\"mountPoints\":[],\"name\":\"celery-beat\",\"portMappings\":[],\"secrets\":[{\"name\":\"DATABASE_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:DATABASE_URL::\"},{\"name\":\"REDIS_URL\",\"valueFrom\":\"arn:aws:secretsmanager:af-south-1:809809510183:secret:watchdog/prod/env-Qthcyi:REDIS_URL::\"}],\"systemControls\":[],\"volumesFrom\":[]}]",
    cpu="128",
    execution_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-execution-role",
    family="watchdog-celery-beat-task",
    memory="128",
    network_mode="bridge",
    region="af-south-1",
    requires_compatibilities=["EC2"],
    task_role_arn="arn:aws:iam::809809510183:role/watchdog-ecs-task-role",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_asg = aws.autoscaling.Group("watchdog_asg",
    availability_zone_distribution={
        "capacity_distribution_strategy": "balanced-best-effort",
    },
    availability_zones=["af-south-1a"],
    capacity_reservation_specification={
        "capacity_reservation_preference": "default",
    },
    default_cooldown=300,
    force_delete=False,
    force_delete_warm_pool=False,
    ignore_failed_scaling_activities=False,
    wait_for_capacity_timeout="10m",
    desired_capacity=1,
    health_check_type="EC2",
    instance_lifecycle_policy={
        "retention_triggers": {
            "terminate_hook_abandon": "terminate",
        },
    },
    instance_maintenance_policy={
        "max_healthy_percentage": 110,
        "min_healthy_percentage": 100,
    },
    launch_template={
        "id": "lt-0ee1b25fe2c86a451",
        "version": "$Default",
    },
    max_size=3,
    min_size=1,
    name="watchdog-prod-asg",
    region="af-south-1",
    service_linked_role_arn="arn:aws:iam::809809510183:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling",
    tags=[{
        "key": "AmazonECSManaged",
        "propagate_at_launch": True,
        "value": "",
    }],
    opts = pulumi.ResourceOptions(protect=True))

watchdog_capacity_provider = aws.ecs.CapacityProvider("watchdog_capacity_provider",
    auto_scaling_group_provider={
        "auto_scaling_group_arn": "arn:aws:autoscaling:af-south-1:809809510183:autoScalingGroup:e55115a6-6164-4e8d-979d-c5e3dda205a8:autoScalingGroupName/watchdog-prod-asg",
        "managed_draining": "ENABLED",
        "managed_scaling": {
            "instance_warmup_period": 300,
            "maximum_scaling_step_size": 10000,
            "minimum_scaling_step_size": 1,
            "status": "ENABLED",
            "target_capacity": 80,
        },
        "managed_termination_protection": "DISABLED",
    },
    name="Infra-ECS-Cluster-watchdog-prod-cluster-AsgCapacityProvider",
    region="af-south-1",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_scaling_target = aws.appautoscaling.Target("watchdog_scaling_target",
    max_capacity=3,
    min_capacity=1,
    region="af-south-1",
    resource_id="service/watchdog-prod-cluster/watchdog-backend-service",
    role_arn="arn:aws:iam::809809510183:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService",
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_scaling_policy = aws.appautoscaling.Policy("watchdog_scaling_policy",
    name="watchdog-backend-cpu-scaling",
    policy_type="TargetTrackingScaling",
    region="af-south-1",
    resource_id="service/watchdog-prod-cluster/watchdog-backend-service",
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
    target_tracking_scaling_policy_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageCPUUtilization",
        },
        "scale_in_cooldown": 120,
        "scale_out_cooldown": 60,
        "target_value": float(35),
    },
    opts = pulumi.ResourceOptions(protect=True))

watchdog_target_group = aws.lb.TargetGroup("watchdog_target_group",
    deregistration_delay=300,
    health_check={
        "healthy_threshold": 5,
        "matcher": "200",
        "path": "/health",
        "protocol": "HTTP",
        "timeout": 5,
        "unhealthy_threshold": 2,
    },
    ip_address_type="ipv4",
    load_balancing_algorithm_type="round_robin",
    load_balancing_anomaly_mitigation="off",
    load_balancing_cross_zone_enabled="use_load_balancer_configuration",
    name="watchdog-target-group",
    port=8000,
    protocol="HTTP",
    protocol_version="HTTP1",
    region="af-south-1",
    stickiness={
        "enabled": False,
        "type": "lb_cookie",
    },
    target_group_health={
        "unhealthy_state_routing": {
            "minimum_healthy_targets_count": "1",
            "minimum_healthy_targets_percentage": "off",
        },
    },
    lambda_multi_value_headers_enabled=False,
    proxy_protocol_v2=False,
    target_type="instance",
    vpc_id="vpc-019ad14bd88b97aae",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_alb = aws.lb.LoadBalancer("watchdog_alb",
    access_logs={
        "bucket": "",
    },
    connection_logs={
        "bucket": "",
    },
    enable_cross_zone_load_balancing=True,
    enable_prefix_for_ipv6_source_nat="off",
    health_check_logs={
        "bucket": "",
    },
    ip_address_type="ipv4",
    load_balancer_type="application",
    name="watchdog-load-balancer",
    region="af-south-1",
    security_groups=["sg-0eb015bd6dce953e1"],
    subnets=[
        "subnet-06e8c222454dfa4c7",
        "subnet-0bd01f1cd19a8eb83",
    ],
    opts = pulumi.ResourceOptions(protect=True))

watchdog_listener_1 = aws.lb.Listener("watchdog_listener_1",
    default_actions=[{
        "order": 1,
        "redirect": {
            "port": "443",
            "protocol": "HTTPS",
            "status_code": "HTTP_301",
        },
        "type": "redirect",
    }],
    load_balancer_arn="arn:aws:elasticloadbalancing:af-south-1:809809510183:loadbalancer/app/watchdog-load-balancer/ce94bef7be924993",
    port=80,
    protocol="HTTP",
    region="af-south-1",
    routing_http_response_server_enabled=True,
    opts = pulumi.ResourceOptions(protect=True))

watchdog_listener_2 = aws.lb.Listener("watchdog_listener_2",
    certificate_arn="arn:aws:acm:af-south-1:809809510183:certificate/29a7cd63-5566-488e-9073-376d68eb7132",
    default_actions=[{
        "forward": {
            "stickiness": {
                "duration": 3600,
            },
            "target_groups": [{
                "arn": "arn:aws:elasticloadbalancing:af-south-1:809809510183:targetgroup/watchdog-target-group/f1fcc819f6e19b5b",
            }],
        },
        "order": 1,
        "target_group_arn": "arn:aws:elasticloadbalancing:af-south-1:809809510183:targetgroup/watchdog-target-group/f1fcc819f6e19b5b",
        "type": "forward",
    }],
    load_balancer_arn="arn:aws:elasticloadbalancing:af-south-1:809809510183:loadbalancer/app/watchdog-load-balancer/ce94bef7be924993",
    mutual_authentication={
        "mode": "off",
    },
    port=443,
    protocol="HTTPS",
    region="af-south-1",
    routing_http_response_server_enabled=True,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_db = aws.rds.Instance("watchdog_db",
    allocated_storage=20,
    availability_zone="af-south-1c",
    backup_retention_period=7,
    backup_target="region",
    backup_window="09:38-10:08",
    ca_cert_identifier="rds-ca-rsa2048-g1",
    copy_tags_to_snapshot=True,
    database_insights_mode="standard",
    db_subnet_group_name="rds-ec2-db-subnet-group-1",
    engine="postgres",
    engine_lifecycle_support="open-source-rds-extended-support-disabled",
    engine_version="18.3",
    identifier="watchdog-db",
    instance_class=aws.rds.InstanceType.T3_MICRO,
    kms_key_id="arn:aws:kms:af-south-1:809809510183:key/eba0a1c9-ac9d-4e65-80a6-c7184dc4294a",
    license_model="postgresql-license",
    maintenance_window="tue:06:36-tue:07:06",
    multi_az=True,
    network_type="IPV4",
    option_group_name="default:postgres-18",
    parameter_group_name="default.postgres18",
    port=5432,
    region="af-south-1",
    skip_final_snapshot=True,
    storage_encrypted=True,
    storage_type=aws.rds.StorageType.GP2,
    username="watchdog",
    vpc_security_group_ids=["sg-04fee3a63fde85564"],
    opts = pulumi.ResourceOptions(protect=True))

watchdog_redis_subnet_group = aws.elasticache.SubnetGroup("watchdog_redis_subnet_group",
    description="Subnet group for watchdog Redis",
    name="watchdog-redis-subnet-group",
    region="af-south-1",
    subnet_ids=[
        "subnet-06e8c222454dfa4c7",
        "subnet-0f86adf9d57b664dc",
    ],
    opts = pulumi.ResourceOptions(protect=True))

watchdog_ecr_repo = aws.ecr.Repository("watchdog_ecr_repo",
    encryption_configurations=[{
        "encryption_type": "AES256",
    }],
    image_scanning_configuration={
        "scan_on_push": False,
    },
    image_tag_mutability="MUTABLE",
    name="watchdog-backend",
    region="af-south-1",
    opts = pulumi.ResourceOptions(protect=True))

watchdog_prod_secret = aws.secretsmanager.Secret("watchdog_prod_secret",
    description="WatchDog production environment variables",
    name="watchdog/prod/env",
    region="af-south-1",
    force_overwrite_replica_secret=False,
    recovery_window_in_days=30,
    opts=pulumi.ResourceOptions(protect=True))

pulumi.export("redis_cluster_id", watchdog_redis.cluster_id)
pulumi.export("watchdog_cluster", watchdog_cluster.name)
pulumi.export("watchdog_backend_service", watchdog_backend_service.name)
pulumi.export("watchdog_vpc", watchdog_vpc.id)
pulumi.export("subnet_1a", subnet_1a.id)
pulumi.export("subnet_1b", subnet_1b.id)
pulumi.export("subnet_1c", subnet_1c.id)
pulumi.export("watchdog_redis_sg", watchdog_redis_sg.id)
pulumi.export("watchdog_ecs_sg", watchdog_ecs_sg.id)
pulumi.export("watchdog_worker_service", watchdog_worker_service.name)
pulumi.export("watchdog_beat_service", watchdog_beat_service.name)
pulumi.export("watchdog_redis_service", watchdog_redis_service.name)
pulumi.export("watchdog_backend_task", watchdog_backend_task.id)
pulumi.export("watchdog_worker_task", watchdog_worker_task.id)
pulumi.export("watchdog_beat_task", watchdog_beat_task.id)
pulumi.export("watchdog_asg", watchdog_asg.id)
pulumi.export("watchdog_capacity_provider", watchdog_capacity_provider.id)
pulumi.export("watchdog_scaling_target", watchdog_scaling_target.id)
pulumi.export("watchdog_scaling_policy", watchdog_scaling_policy.id)
pulumi.export("watchdog_target_group", watchdog_target_group.id)
pulumi.export("watchdog_alb", watchdog_alb.id)
pulumi.export("watchdog_listener_1", watchdog_listener_1.id)
pulumi.export("watchdog_listener_2", watchdog_listener_2.id)
pulumi.export("watchdog_db", watchdog_db.id)
pulumi.export("watchdog_redis_subnet_group", watchdog_redis_subnet_group.id)
pulumi.export("watchdog_ecr_repo", watchdog_ecr_repo.id)
