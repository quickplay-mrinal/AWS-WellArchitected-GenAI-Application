import pulumi
import pulumi_aws as aws
import json

# Configuration
config = pulumi.Config()
aws_config = pulumi.Config("aws")
region = aws_config.get("region") or "ap-southeast-1"

# Create provider for us-east-1 (required for CloudFront WAF)
us_east_1_provider = aws.Provider("us-east-1-provider", region="us-east-1")

# Use specific VPC
vpc_id = "vpc-0df24266608a12b69"
vpc = aws.ec2.get_vpc(id=vpc_id)

# Get all subnets in the VPC
all_subnets = aws.ec2.get_subnets(filters=[aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[vpc_id])])

# Filter subnets to get only one per AZ (for ALB requirement)
def get_unique_az_subnets(subnet_ids):
    """Get one subnet per availability zone"""
    import boto3
    ec2 = boto3.client('ec2', region_name=region)
    
    subnets_response = ec2.describe_subnets(SubnetIds=subnet_ids)
    az_subnet_map = {}
    
    for subnet in subnets_response['Subnets']:
        az = subnet['AvailabilityZone']
        subnet_id = subnet['SubnetId']
        # Prefer public subnets (with MapPublicIpOnLaunch=True)
        if az not in az_subnet_map or subnet.get('MapPublicIpOnLaunch', False):
            az_subnet_map[az] = subnet_id
    
    return list(az_subnet_map.values())

# Get unique AZ subnets for ALB
vpc_subnets_for_alb = get_unique_az_subnets(all_subnets.ids)

# Use all subnets for ECS tasks
vpc_subnets = all_subnets

# DynamoDB Table with Point-in-Time Recovery
dynamodb_table = aws.dynamodb.Table(
    "wellarchitected-app-table",
    name="WellArchitectedApp",
    billing_mode="PAY_PER_REQUEST",
    hash_key="PK",
    range_key="SK",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="PK", type="S"),
        aws.dynamodb.TableAttributeArgs(name="SK", type="S"),
        aws.dynamodb.TableAttributeArgs(name="GSI1PK", type="S"),
        aws.dynamodb.TableAttributeArgs(name="GSI1SK", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="GSI1",
            hash_key="GSI1PK",
            range_key="GSI1SK",
            projection_type="ALL",
        )
    ],
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
        enabled=True,
    ),
    tags={"Environment": "production", "Application": "WellArchitectedGenAI"},
)

# S3 Bucket for Well-Architected Documents
import random
import string
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
docs_bucket = aws.s3.BucketV2(
    "wellarchitected-docs-bucket",
    bucket=f"wellarchitected-docs-{region}-{random_suffix}",
    tags={"Environment": "production", "Purpose": "KnowledgeBase"},
)

docs_bucket_versioning = aws.s3.BucketVersioningV2(
    "docs-bucket-versioning",
    bucket=docs_bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(status="Enabled"),
)

docs_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "docs-bucket-public-access-block",
    bucket=docs_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# S3 Bucket for Reports
reports_bucket = aws.s3.BucketV2(
    "wellarchitected-reports-bucket",
    bucket=f"wellarchitected-reports-{region}-{random_suffix}",
    tags={"Environment": "production", "Purpose": "Reports"},
)

reports_bucket_versioning = aws.s3.BucketVersioningV2(
    "reports-bucket-versioning",
    bucket=reports_bucket.id,
    versioning_configuration=aws.s3.BucketVersioningV2VersioningConfigurationArgs(status="Enabled"),
)

reports_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "reports-bucket-public-access-block",
    bucket=reports_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# ECR Repository for Backend
backend_ecr = aws.ecr.Repository(
    "backend-ecr",
    name="wellarchitected-backend",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(scan_on_push=True),
    image_tag_mutability="MUTABLE",
)

# ECR Repository for Frontend
frontend_ecr = aws.ecr.Repository(
    "frontend-ecr",
    name="wellarchitected-frontend",
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(scan_on_push=True),
    image_tag_mutability="MUTABLE",
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    "wellarchitected-cluster",
    name="WellArchitectedCluster",
    settings=[aws.ecs.ClusterSettingArgs(name="containerInsights", value="enabled")],
)

# CloudWatch Log Groups
backend_log_group = aws.cloudwatch.LogGroup(
    "backend-logs",
    name="/ecs/wellarchitected-backend",
    retention_in_days=7,
)

frontend_log_group = aws.cloudwatch.LogGroup(
    "frontend-logs",
    name="/ecs/wellarchitected-frontend",
    retention_in_days=7,
)

# IAM Role for ECS Task Execution
ecs_task_execution_role = aws.iam.Role(
    "ecs-task-execution-role",
    name="WellArchitectedECSTaskExecutionRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

aws.iam.RolePolicyAttachment(
    "ecs-task-execution-policy",
    role=ecs_task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# Grant ECS task execution role access to Secrets Manager (for pulling secrets at container startup)
ecs_task_execution_secrets_policy = aws.iam.RolePolicy(
    "ecs-task-execution-secrets-policy",
    role=ecs_task_execution_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["secretsmanager:GetSecretValue"],
            "Resource": "arn:aws:secretsmanager:*:*:secret:wellarchitected/*",
        }],
    }),
)

# IAM Role for ECS Task (Application)
ecs_task_role = aws.iam.Role(
    "ecs-task-role",
    name="WellArchitectedECSTaskRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

# IAM Policy for ECS Task
ecs_task_policy = aws.iam.RolePolicy(
    "ecs-task-policy",
    role=ecs_task_role.id,
    policy=pulumi.Output.all(dynamodb_table.arn, docs_bucket.arn, reports_bucket.arn).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["dynamodb:*"],
                    "Resource": [args[0], f"{args[0]}/index/*"],
                },
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": [args[1], f"{args[1]}/*", args[2], f"{args[2]}/*"],
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel", "bedrock:Retrieve", "bedrock:RetrieveAndGenerate"],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["ec2:Describe*", "rds:Describe*", "lambda:*", "iam:*", "cloudwatch:*", "config:*", "wellarchitected:*"],
                    "Resource": "*",
                },
            ],
        })
    ),
)

# Security Group for ALB
alb_security_group = aws.ec2.SecurityGroup(
    "alb-sg",
    name="wellarchitected-alb-sg",
    description="Security group for Application Load Balancer",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"]),
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=443, to_port=443, cidr_blocks=["0.0.0.0/0"]),
    ],
    egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
)

# Security Group for ECS Tasks
ecs_security_group = aws.ec2.SecurityGroup(
    "ecs-sg",
    name="wellarchitected-ecs-sg",
    description="Security group for ECS tasks",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=8000, to_port=8000, security_groups=[alb_security_group.id]),
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=3000, to_port=3000, security_groups=[alb_security_group.id]),
    ],
    egress=[aws.ec2.SecurityGroupEgressArgs(protocol="-1", from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])],
)

# Application Load Balancer (use unique AZ subnets)
alb = aws.lb.LoadBalancer(
    "wellarchitected-alb",
    name="wellarchitected-alb",
    load_balancer_type="application",
    security_groups=[alb_security_group.id],
    subnets=vpc_subnets_for_alb,
    enable_deletion_protection=False,
)

# Target Group for Backend
backend_target_group = aws.lb.TargetGroup(
    "backend-tg",
    name="wellarchitected-backend-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
)

# Target Group for Frontend
frontend_target_group = aws.lb.TargetGroup(
    "frontend-tg",
    name="wellarchitected-frontend-tg",
    port=3000,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
)

# ALB Listener
alb_listener = aws.lb.Listener(
    "alb-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=frontend_target_group.arn,
    )],
)

# ALB Listener Rule for Backend API
backend_listener_rule = aws.lb.ListenerRule(
    "backend-rule",
    listener_arn=alb_listener.arn,
    priority=100,
    conditions=[aws.lb.ListenerRuleConditionArgs(path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(values=["/api/*"]))],
    actions=[aws.lb.ListenerRuleActionArgs(type="forward", target_group_arn=backend_target_group.arn)],
)

# Secrets Manager for sensitive environment variables (must be defined before task definition)
backend_secrets = aws.secretsmanager.Secret(
    "backend-secrets",
    name="wellarchitected/backend/secrets",
    description="Backend application secrets",
)

backend_secret_version = aws.secretsmanager.SecretVersion(
    "backend-secret-version",
    secret_id=backend_secrets.id,
    secret_string=json.dumps({
        "SECRET_KEY": "change-this-in-production",
        "ENCRYPTION_KEY": "change-this-in-production",
        "BEDROCK_INFERENCE_PROFILE_ARN": "arn:aws:bedrock:ap-south-1:892345653395:inference-profile/apac.anthropic.claude-sonnet-4-5-20250929-v1:0",
    }),
)

# ECS Task Definition for Backend
backend_task_definition = aws.ecs.TaskDefinition(
    "backend-task",
    family="wellarchitected-backend",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    cpu="1024",
    memory="2048",
    execution_role_arn=ecs_task_execution_role.arn,
    task_role_arn=ecs_task_role.arn,
    container_definitions=pulumi.Output.all(backend_ecr.repository_url, backend_log_group.name, region, dynamodb_table.name, docs_bucket.bucket, reports_bucket.bucket, backend_secrets.arn).apply(
        lambda args: json.dumps([{
            "name": "backend",
            "image": f"{args[0]}:latest",
            "essential": True,
            "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
            "environment": [
                {"name": "AWS_REGION", "value": args[2]},
                {"name": "DYNAMODB_TABLE_NAME", "value": args[3]},
                {"name": "S3_DOCS_BUCKET", "value": args[4]},
                {"name": "S3_REPORTS_BUCKET", "value": args[5]},
                {"name": "BEDROCK_MODEL_ID", "value": "anthropic.claude-sonnet-4-5-20250929-v1:0"},
                {"name": "ENVIRONMENT", "value": "production"},
            ],
            "secrets": [
                {"name": "SECRET_KEY", "valueFrom": f"{args[6]}:SECRET_KEY::"},
                {"name": "ENCRYPTION_KEY", "valueFrom": f"{args[6]}:ENCRYPTION_KEY::"},
                {"name": "BEDROCK_INFERENCE_PROFILE_ARN", "valueFrom": f"{args[6]}:BEDROCK_INFERENCE_PROFILE_ARN::"},
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": args[1],
                    "awslogs-region": args[2],
                    "awslogs-stream-prefix": "backend",
                },
            },
        }])
    ),
)

# ECS Service for Backend with Auto Scaling
backend_service = aws.ecs.Service(
    "backend-service",
    name="wellarchitected-backend-service",
    cluster=ecs_cluster.arn,
    task_definition=backend_task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=vpc_subnets.ids,
        security_groups=[ecs_security_group.id],
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=backend_target_group.arn,
        container_name="backend",
        container_port=8000,
    )],
    opts=pulumi.ResourceOptions(depends_on=[alb_listener]),
)

# Auto Scaling Target for Backend
backend_scaling_target = aws.appautoscaling.Target(
    "backend-scaling-target",
    max_capacity=10,
    min_capacity=2,
    resource_id=pulumi.Output.concat("service/", ecs_cluster.name, "/", backend_service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

# Auto Scaling Policy - CPU
backend_cpu_scaling = aws.appautoscaling.Policy(
    "backend-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=backend_scaling_target.resource_id,
    scalable_dimension=backend_scaling_target.scalable_dimension,
    service_namespace=backend_scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageCPUUtilization",
        ),
        target_value=70.0,
        scale_in_cooldown=300,
        scale_out_cooldown=60,
    ),
)

# Auto Scaling Policy - Memory
backend_memory_scaling = aws.appautoscaling.Policy(
    "backend-memory-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=backend_scaling_target.resource_id,
    scalable_dimension=backend_scaling_target.scalable_dimension,
    service_namespace=backend_scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageMemoryUtilization",
        ),
        target_value=80.0,
        scale_in_cooldown=300,
        scale_out_cooldown=60,
    ),
)

# ECS Task Definition for Frontend
frontend_task_definition = aws.ecs.TaskDefinition(
    "frontend-task",
    family="wellarchitected-frontend",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    cpu="512",
    memory="1024",
    execution_role_arn=ecs_task_execution_role.arn,
    container_definitions=pulumi.Output.all(frontend_ecr.repository_url, frontend_log_group.name, region, alb.dns_name).apply(
        lambda args: json.dumps([{
            "name": "frontend",
            "image": f"{args[0]}:latest",
            "essential": True,
            "portMappings": [{"containerPort": 3000, "protocol": "tcp"}],
            "environment": [
                {"name": "NEXT_PUBLIC_API_URL", "value": f"http://{args[3]}/api"},
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": args[1],
                    "awslogs-region": args[2],
                    "awslogs-stream-prefix": "frontend",
                },
            },
        }])
    ),
)

# ECS Service for Frontend with Auto Scaling
frontend_service = aws.ecs.Service(
    "frontend-service",
    name="wellarchitected-frontend-service",
    cluster=ecs_cluster.arn,
    task_definition=frontend_task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=True,
        subnets=vpc_subnets.ids,
        security_groups=[ecs_security_group.id],
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=frontend_target_group.arn,
        container_name="frontend",
        container_port=3000,
    )],
    opts=pulumi.ResourceOptions(depends_on=[alb_listener]),
)

# Auto Scaling Target for Frontend
frontend_scaling_target = aws.appautoscaling.Target(
    "frontend-scaling-target",
    max_capacity=10,
    min_capacity=2,
    resource_id=pulumi.Output.concat("service/", ecs_cluster.name, "/", frontend_service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

# Auto Scaling Policy for Frontend
frontend_cpu_scaling = aws.appautoscaling.Policy(
    "frontend-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=frontend_scaling_target.resource_id,
    scalable_dimension=frontend_scaling_target.scalable_dimension,
    service_namespace=frontend_scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageCPUUtilization",
        ),
        target_value=70.0,
        scale_in_cooldown=300,
        scale_out_cooldown=60,
    ),
)

# Outputs
pulumi.export("vpc_id", vpc_id)
pulumi.export("dynamodb_table_name", dynamodb_table.name)
pulumi.export("docs_bucket_name", docs_bucket.bucket)
pulumi.export("reports_bucket_name", reports_bucket.bucket)
pulumi.export("backend_ecr_url", backend_ecr.repository_url)
pulumi.export("frontend_ecr_url", frontend_ecr.repository_url)
pulumi.export("ecs_cluster_name", ecs_cluster.name)
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("application_url", pulumi.Output.concat("http://", alb.dns_name))
pulumi.export("api_url", pulumi.Output.concat("http://", alb.dns_name, "/api"))
pulumi.export("region", region)


# ============================================
# PRODUCTION ENHANCEMENTS
# ============================================
# Note: Secrets Manager resources moved earlier in the file before task definition
# ============================================

# Note: DynamoDB Point-in-Time Recovery is configured in the table definition above
# PITR is enabled by default in the table resource

# CloudFront Distribution for Frontend
cloudfront_oai = aws.cloudfront.OriginAccessIdentity(
    "cloudfront-oai",
    comment="OAI for WellArchitected Frontend",
)

cloudfront_distribution = aws.cloudfront.Distribution(
    "frontend-cdn",
    enabled=True,
    is_ipv6_enabled=True,
    comment="WellArchitected Frontend CDN",
    default_root_object="index.html",
    origins=[
        aws.cloudfront.DistributionOriginArgs(
            domain_name=alb.dns_name,
            origin_id="alb-origin",
            custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
                http_port=80,
                https_port=443,
                origin_protocol_policy="http-only",
                origin_ssl_protocols=["TLSv1.2"],
            ),
        )
    ],
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
        cached_methods=["GET", "HEAD"],
        target_origin_id="alb-origin",
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=True,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="all",
            ),
            headers=["*"],
        ),
        viewer_protocol_policy="redirect-to-https",
        min_ttl=0,
        default_ttl=0,
        max_ttl=0,
        compress=True,
    ),
    price_class="PriceClass_100",
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ),
)

# WAF Web ACL for CloudFront (must be in us-east-1)
waf_ip_set = aws.wafv2.IpSet(
    "waf-ip-set",
    name="wellarchitected-allowed-ips",
    scope="CLOUDFRONT",
    ip_address_version="IPV4",
    addresses=[],  # Add your allowed IPs here
    opts=pulumi.ResourceOptions(provider=us_east_1_provider),
)

waf_web_acl = aws.wafv2.WebAcl(
    "waf-web-acl",
    name="wellarchitected-waf",
    scope="CLOUDFRONT",
    opts=pulumi.ResourceOptions(provider=us_east_1_provider),
    default_action=aws.wafv2.WebAclDefaultActionArgs(allow={}),
    rules=[
        # Rate limiting rule
        aws.wafv2.WebAclRuleArgs(
            name="rate-limit-rule",
            priority=1,
            action=aws.wafv2.WebAclRuleActionArgs(block={}),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                rate_based_statement=aws.wafv2.WebAclRuleStatementRateBasedStatementArgs(
                    limit=2000,
                    aggregate_key_type="IP",
                )
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="RateLimitRule",
                sampled_requests_enabled=True,
            ),
        ),
        # AWS Managed Rules - Core Rule Set
        aws.wafv2.WebAclRuleArgs(
            name="aws-managed-rules-core",
            priority=2,
            override_action=aws.wafv2.WebAclRuleOverrideActionArgs(none={}),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                    vendor_name="AWS",
                    name="AWSManagedRulesCommonRuleSet",
                )
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="AWSManagedRulesCore",
                sampled_requests_enabled=True,
            ),
        ),
        # AWS Managed Rules - Known Bad Inputs
        aws.wafv2.WebAclRuleArgs(
            name="aws-managed-rules-known-bad-inputs",
            priority=3,
            override_action=aws.wafv2.WebAclRuleOverrideActionArgs(none={}),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                    vendor_name="AWS",
                    name="AWSManagedRulesKnownBadInputsRuleSet",
                )
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="AWSManagedRulesKnownBadInputs",
                sampled_requests_enabled=True,
            ),
        ),
    ],
    visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
        cloudwatch_metrics_enabled=True,
        metric_name="WellArchitectedWAF",
        sampled_requests_enabled=True,
    ),
)

# CloudWatch Alarms
# Backend CPU Alarm
backend_cpu_alarm = aws.cloudwatch.MetricAlarm(
    "backend-cpu-alarm",
    name="wellarchitected-backend-high-cpu",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="CPUUtilization",
    namespace="AWS/ECS",
    period=300,
    statistic="Average",
    threshold=80,
    alarm_description="Backend CPU utilization is too high",
    dimensions={
        "ClusterName": ecs_cluster.name,
        "ServiceName": backend_service.name,
    },
)

# Backend Memory Alarm
backend_memory_alarm = aws.cloudwatch.MetricAlarm(
    "backend-memory-alarm",
    name="wellarchitected-backend-high-memory",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="MemoryUtilization",
    namespace="AWS/ECS",
    period=300,
    statistic="Average",
    threshold=85,
    alarm_description="Backend memory utilization is too high",
    dimensions={
        "ClusterName": ecs_cluster.name,
        "ServiceName": backend_service.name,
    },
)

# ALB Target Health Alarm
alb_unhealthy_targets_alarm = aws.cloudwatch.MetricAlarm(
    "alb-unhealthy-targets",
    name="wellarchitected-alb-unhealthy-targets",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="UnHealthyHostCount",
    namespace="AWS/ApplicationELB",
    period=60,
    statistic="Average",
    threshold=0,
    alarm_description="ALB has unhealthy targets",
    dimensions={
        "LoadBalancer": alb.arn_suffix,
        "TargetGroup": backend_target_group.arn_suffix,
    },
)

# Note: CodeBuild removed - using GitHub Actions for CI/CD instead

# Additional Outputs for Production Features
pulumi.export("secrets_manager_arn", backend_secrets.arn)
pulumi.export("cloudfront_domain", cloudfront_distribution.domain_name)
pulumi.export("cloudfront_url", pulumi.Output.concat("https://", cloudfront_distribution.domain_name))
pulumi.export("waf_web_acl_id", waf_web_acl.id)
