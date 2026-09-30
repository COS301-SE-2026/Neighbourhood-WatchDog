# Neighbourhood WatchDog

## Technical Deployment Document

Team Intrepid · COS 301 Capstone Project · University of Pretoria

In partnership with EPI-USE Africa

Version 2.0 · 2026

---

## 1. Overview
This document provides a complete technical reference for deploying, configuring, and maintaining the Neighbourhood WatchDog platform in a production environment.

The system is deployed on AWS in the **Africa (Cape Town) `af-south-1`** region and is accessible at `neighbourhoodwatchdog.co.za`. The backend runs as containerised ECS tasks on **EC2 launch type** (behind an Auto Scaling Group and capacity provider **not Fargate**) behind an Application Load Balancer. The frontend is deployed separately on **Vercel**. DNS is managed through **GoDaddy** (not Route 53). Push notifications are delivered via **Firebase Cloud Messaging**.

## 2. Architecture Overview

### Components
- **Frontend** Next.js, hosted on Vercel (managed edge, outside AWS).
- **Backend** FastAPI, running as ECS tasks on **EC2 launch type** (`backend#1`, `backend#2`, currently 2 tasks, auto-scaling 2–3 on backend CPU), behind an ALB. **Per-task AZ placement is not confirmed** check `aws ecs describe-tasks` before stating it.
- **Celery worker** 1 ECS task (EC2 launch type). AZ placement not confirmed.
- **Celery beat** a single ECS task (singleton scheduler, EC2 launch type). AZ placement not confirmed running more than one instance would duplicate scheduled jobs.
- **Database** Amazon RDS for PostgreSQL 16 with PostGIS (`watchdog-db`), instance class `db.t3.micro`. **Multi-AZ is disabled no standby.**
- **Cache / broker** Amazon ElastiCache for Redis (`watchdog-redis`), `cache.t4g.micro`, **single node, no replica**, serving as both the Celery broker and the application cache. A failure here takes out caching and task queueing simultaneously.
- **Media relay** a standalone EC2 instance (outside ECS), confirmed running **MediaMTX**, handling RTSP ingest and WebRTC egress. No ASG, no standby a single instance.
- **Edge Agents** Python agents running on-premise (physical access outside our control), pulling RTSP from cameras and syncing with the backend/media EC2 instance.
- **Mobile app** Capacitor Android shell wrapping the web dashboard, plus background-geolocation pings for officer location.
- **Push notifications** Firebase Cloud Messaging, triggered by a `send_push_to_users` Celery task via the Firebase Admin SDK.
- **Secrets** AWS Secrets Manager, `watchdog/prod/env`.
- **Container registry** Amazon ECR, `watchdog-backend`.
- **Auth** AWS Cognito User Pool (regional service).
- **DNS** GoDaddy.

### Network Layout
- VPC: `watchdog-vpc`, CIDR `10.0.0.0/16`.
- Subnets, one per AZ (each an independent failure domain):
  - `watchdog-subnet-1a` `10.0.1.0/24` (`af-south-1a`)
  - `watchdog-subnet-1b` `10.0.2.0/24` (`af-south-1b`)
  - `watchdog-subnet-1c` `10.0.3.0/24` (`af-south-1c`)
- RDS and ElastiCache subnet groups: **confirmed `subnet_a` + `subnet_b` (AZ `1a` + `1b`) only** `1c` is not included in either.
- The whole `af-south-1` production account sits behind a trust boundary at the public-internet edge; a second internal trust boundary separates the ECS compute tier from the data tier (RDS/ElastiCache/media EC2).

### Traffic Flow
- **Control plane**: residents/officers (browser or mobile app) and Edge Agents reach the platform over HTTPS (TLS 1.3) via the **`watchdog-load-balancer`** ALB, which terminates TLS with an ACM certificate, redirects HTTP (80) → HTTPS (443), and load-balances across the backend ECS tasks (health-checked over HTTP at `/health`).
- **Media plane**: Edge Agents push RTSP streams (with HMAC-derived per-camera credential) directly to the standalone media EC2 instance (RTSP `:8554`); that instance serves WebRTC out on `:8889` (plus ICE/UDP on `:8189`) and exposes its internal API on **`:9997`**, restricted to `127.0.0.1` only (not reachable over the network at all bound to loopback inside the container, so no security-group rule is what makes it private, the bind address itself is).
- **Frontend**: served independently from Vercel's edge network; talks to the backend over HTTPS via the ALB.
- **DNS**: resolved through GoDaddy not Route 53.
- **Push notifications**: the backend/Celery layer syncs with Firebase Cloud Messaging (Google-operated, outside AWS) via the Firebase Admin SDK to deliver notifications to the mobile app.
- **Data tier**: only the ECS tasks (backend, celery-worker, celery-beat) can reach RDS and ElastiCache; neither is reachable from the public internet.

## 3. Prerequisites

### Deployment Machine
- Git
- AWS CLI (configured for the production account, `af-south-1`)
- SSH access to the media EC2 instance
- Access to push images to ECR (`watchdog-backend`)
- Access to register/update ECS task definitions and services
- Vercel CLI or dashboard access for frontend deploys

### Media EC2 Instance
- Ubuntu Ubuntu 22.04.5 LTS, not established this session
- Docker Engine
- Docker Compose v2
- Git

### ECS (Backend / Celery) - EC2 launch type, not Fargate
Unlike Fargate, EC2 launch type has real host-level prerequisites, managed via an Auto Scaling Group and ECS capacity provider:
- An ASG (`watchdog-prod-asg`) running ECS-optimized AMI instances, with a capacity provider (`watchdog-capacity-provider`) doing managed scaling
- A built and pushed image in ECR (`watchdog-backend`)
- Task definitions for `backend`, `celery-worker`, and `celery-beat`
- IAM task role with permission to read `watchdog/prod/env` from Secrets Manager (and, for the backend task specifically, an inline S3 policy for clip uploads `s3-clips-access`)

### Frontend (Vercel)
- Project linked to the repository
- Environment variables configured in the Vercel project settings

## 4. Infrastructure - AWS Setup

### VPC
- `watchdog-vpc` `10.0.0.0/16`, spanning `af-south-1a`, `af-south-1b`, `af-south-1c`.
- One subnet per AZ, as listed in §2.

### Application Load Balancer
- **`watchdog-load-balancer`** public-facing, registered subnets/AZ span not independently re-verified this revision; confirm before stating "spans all 3 AZs."
- Listener: HTTP `:80` → redirect to HTTPS `:443`.
- Listener: HTTPS `:443`, ACM-issued certificate.
- Target group (`watchdog-target-group`): the `backend` ECS tasks only, health-checked over HTTP at `/health`. **`celery-worker` and `celery-beat` are never registered with this or any target group.**

### ECS Cluster
- Launch type: **EC2** (not Fargate).
- Services:
  - `backend` currently 2 tasks, auto-scaling 2–3 on backend CPU (target-tracking, 60% target), 1024 CPU / 1024 MiB memory each, registered behind the ALB target group.
  - `celery-worker` 1 task.
  - `celery-beat` a single task (must remain a singleton running more than one instance will duplicate scheduled jobs).

### RDS
- `watchdog-db` PostgreSQL 16 with PostGIS, `db.t3.micro`.
- Multi-AZ: **disabled** no standby.
- `skip_final_snapshot = true`, deletion protection: **disabled**.
- Only reachable from the ECS task security group.
- Subnet group: `subnet_a` + `subnet_b` (AZ `1a` + `1b`) only.

### ElastiCache
- `watchdog-redis` `cache.t4g.micro`, used as both the Celery broker and application cache.
- **Single node, no replica** a real single point of failure; losing this node loses caching and task queueing at the same time.
- Only reachable from the ECS task security group.
- Subnet group: `subnet_a` + `subnet_b` (AZ `1a` + `1b`) only.

### Media EC2 Instance
- Standalone EC2 instance (outside the ECS cluster), confirmed running **MediaMTX**.
- Public IP: **`13.247.60.206`** **not an Elastic IP**; will change if the instance is ever stopped and started (not on a simple reboot). Consider allocating a real Elastic IP to remove this risk.
- Ports: `22` (admin, currently `0.0.0.0/0` deliberate, for CI reachability, key-auth gated), `8554` (RTSP), `8189/udp` (WebRTC ICE), `8889` (WebRTC), `9997` (internal API, `127.0.0.1` only, not exposed on the network interface at all).

### Security Group Rules (per component do not use one flat rule set)
| Security Group | Inbound | From |
|---|---|---|
| ALB SG | 80, 443 | Public internet |
| ECS `backend` task SG | HTTP (health/app port) | ALB SG only |
| ECS `celery-worker`/`celery-beat` task SG | (no inbound app rule; not behind the ALB) | |
| RDS SG | 5432 | ECS task SG only |
| ElastiCache SG | 6379 | ECS task SG only |
| Media EC2 SG | 8554, 8189/udp, 8889 | Public internet (RTSP/WebRTC) |
| Media EC2 SG | 9997 | Not exposed bound to `127.0.0.1` inside the container; no SG rule makes this reachable regardless of what's configured |
| Media EC2 SG | 22 | `0.0.0.0/0` (deliberate, for CI reachability; key-auth gated) |

### AWS Cognito
- User Pool in `af-south-1`.
- Enable MFA (TOTP).
- Configure App Client.
- Create the required user groups.

### AWS Secrets Manager
- Secret: `watchdog/prod/env` holds production environment variables (DB connection string, Redis connection string, Cognito config, Firebase Admin credentials, RTSP encryption key, etc.). Referenced by ECS task definitions, not baked into images.

### Amazon ECR
- Repository: `watchdog-backend` backend Docker images are built and pushed here, then referenced by ECS task definitions.

### Domain and SSL
- DNS is managed in **GoDaddy**, pointing `neighbourhoodwatchdog.co.za` (and the `api.`/`stream.` subdomains) at the ALB and the media EC2 instance respectively.
- TLS for the backend/frontend path is terminated at the ALB via ACM.
- TLS for the media relay's WebRTC path is terminated **by MediaMTX itself**, via certs mounted into the container and referenced directly in its config
