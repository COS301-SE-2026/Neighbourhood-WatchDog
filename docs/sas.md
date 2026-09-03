# Software Architecture Specification (SAS)
# Neighbourhood WatchDog

version 3.1 Updated 3 September 2026 

# 1. Introduction

This Software Architecture Specification (SAS) document describes the architectural design of the Neighbourhood WatchDog system. It outlines the system's major components, their responsibilities, interactions, and the technologies used to implement them. The document serves as a reference for developers, stakeholders, and maintainers by providing a comprehensive overview of the software architecture and the rationale behind key design decisions.

The architecture of Neighbourhood WatchDog is organised into six primary subsystems: Video Ingestion, AI Detection Engine, Alert and Event Management, User and Access Control, Monitoring Dashboard, and Data and Storage Management. Together, these subsystems provide a modular and scalable foundation capable of supporting real-time video processing, secure user management, and reliable data persistence. Technologies such as MediaMTX, FFmpeg, YOLOv8, DeepSORT, FastAPI, WebSockets, Next.js, PostgreSQL, AWS Cognito, and Amazon S3 are utilised to ensure the system remains performant, extensible, and suitable for deployment in community-based security environments.

# 1.1 Purpose
The purpose of this document is to communicate the architectural structure of the system, define the relationships between its components, and establish a shared understanding of the design principles that guide its implementation and future evolution.


# 2. Architectural Requirements
### 2.1 Architectural patterns
| Pattern | Application in WatchDog | Purpose | Rationale |
|---|---|---|---|
| Client–server | Next.js browser client consumes FastAPI REST/WebSocket services. | The Next.js frontend communicates with backend APIs and WebSocket services through a client-server model. | Separates interaction/UI from domain and persistence concerns. |
| Event-driven | Detection/annotation posts result in backend WebSocket broadcast to browser clients. | Real-time stream processing enables asynchronous communication between video ingestion, AI detection services, and alert management. | Supports live operational updates without refresh polling. |

### 2.2 Design Patterns
| Design Pattern | Implementation |
|---|---|
| Strategy | The AI detection worker can delegate frame analysis to a selected detection strategy. The current implementation uses YOLO-based person and weapon detection with DeepSORT tracking. Future strategies can support vehicle, fall, loitering, or perimeter-intrusion detection without changing the camera runtime’s overall workflow. |
| Observer | When an AI worker posts a detection or annotation to the FastAPI backend, the backend broadcasts alert and annotation updates through WebSockets. Dashboard clients subscribed through WebSocket connections receive updates immediately and refresh alerts or bounding-box overlays without polling. |
| State | The camera playback UI moves between distinct states: `connecting`, `live`, and `unavailable/offline`. When a user selects a camera, the frontend initiates WHEP/WebRTC playback and displays the appropriate state based on connection success, stream availability, or failure. Closing the camera view ends the playback session and returns the component to its initial state. Moreover, the Edge Agent also moves between distinct states: `setup`, `running` and `off`.|
| Factory | A factory can centralise creation of camera-specific runtime components. Given a camera configuration, it would construct the corresponding FFmpeg publisher, AI detection worker, credentials, stream path, and process configuration. |
| Chain of Responsibility | Requests pass through sequential validation and authorisation stages: authentication, role/property access checks, request validation, internal-agent token validation, and finally route/service execution. FastAPI middleware and dependency functions naturally support this pattern. |
| Command | Camera actions such as enable, disable, start publisher, stop publisher, start detection, and stop detection, can be represented as commands. This would make operations easier to queue, retry, log, audit, and potentially execute remotely through the WatchDog Agent. |

### 2.3 Architectural Constraints
- Existing CCTV and IP cameras must provide RTSP streams.
- Processing multiple video streams simultaneously can be computationally expensive and doing this in the cloud can incur a great monetary cost, further, doing it locally may be slow due to hardware limitations of the user's machine.
- Real-time video processing must minimize latency while supporting multiple concurrent streams.
- Sensitive information must remain encrypted during transmission.
- Secrets and credentials may not be committed to source control.
- All deployments must be reproducible using Infrastructure as Code and containerization technologies.
- The system must support independent scaling of AI processing services.
- Production deployments must remain accessible through public URLs.
- Services must support horizontal scalability where appropriate.

### 2.4 Architectural Diagram
![Architecture Diagramv2](/docs/images/Architecture%20Diagramv3.svg)

### 2.5 Mapping Quality Requirements to Architectural Decisions
|Quality Requirement|Architectural Decision|
|---|---|
|Availability: >= 99.5% uptime|Made use of a load balancer as well as multi-AZ database deployment|
|Performance: Support for 500+ concurrent users|Deployed with ECS, AWS' contanerised management service deployed with automatic scaling policies|
|Data encryption for sensitve information|Use of AWS RDS and AWS Secrets Manager both of which encrypt data at rest using AES-256 and TLS 1.3 for secure communication between services. Moreover, MFA is used through AWS Cognito|
|Reliability: Recovery within 5 minutes after failure|Automated backups, failover replication, and monitoring with automated recovery scripts.|
|Scalability: support for up to 200% workload increase without major architectural changes|ECS with an Application Load Balancer allows horizontal scaling by increasing the service's desired task count with no architecture changes. The underlying EC2 ASG (auto scalaing group) scales out to provide for additional tasks|
|Maintainability: new features/fixes deployable within 2 hours|CI/CD via GitHub Actions automates images build, ECR push and ECS service update on every push to the `main` branch of the repository. Deployments complete within a matter of minutes|

# 3. Technology Requirements

### 3.1 Frontend Technologies
| Technology | Role | Justification |
|---|---|---|
| Next.js, React, TypeScript | Web Dashboard | Typed component-based UI with route structure suitable for public/private flows. |
| Tailwind CSS | Styling | Supports consistent styles and responsive design. |
| WebSockets | Real-Time Communication | Supports live alert updates |

### 3.2 Backend Technologies
| Technology | Role | Justification |
|---|---|---|
| FastAPI | REST/WebSocket API and domain logic | High-performance asynchronous APIs. |
| Python | Backend Development | Extensive AI and computer vision ecosystem. |
| Node.js | Supporting Services | Efficient event-driven processing. |
| SQLAlchemy | ORM | Simplifies database interactions. |


### 3.3 AI Technologies
| Technology | Role | Justification |
|---|---|---|
| YOLOv8 | Object Detectioon | Provides baseline visual detection/tracking at edge. |
| DeepSort | Object Tracking | Person detection and within-stream tracking. |
| OpenCV | Image Processing | Provides a robust, high-performance foundation for handling image and video data before and during model inference. |
| PyTorch | Machine Learning Framework | PyTorch is an ideal framework for building and deploying AI detection systems due to its flexibility, dynamic computation, and rich ecosystem of pre-trained vision and NLP models. |

### 3.4 Infrastructure Technologies
| Technology | Role | Justification |
|---|---|---|
| Docker Compose, Caddy | Reproducible container runtime and API TLS/reverse proxy | Supports local and EC2 runtime topology. |
| GitHub Actions, Vercel | CI and frontend deployment | Automates validation and public frontend deployment. |
| MediaMTX | Stream relay and WHEP/WebRTC egress | Separates source camera from consumers; provides low-latency browser protocol. |
| FFmpeg | Camera source conversion and relay publication | Mature protocol support for heterogeneous RTSP inputs. |
| Redis | Caching and Background Processing | Delivers the ultra-low latency, high-throughput messaging, and real-time state management required to process live video frames and trigger instant alerts. |
| Amazon S3 | Video Clip Storage | Provides cheap, reliable, and scalable storage that easily connects to AI and video processing tools. |
| AWS Cognito | Authentication and Authorization | Handles user registration, secure login, password resets, and multi-factor authentication (MFA). |

### 3.5 Technology Selection Rationale

The selected technologies collectively support:

- High availability
- Horizontal scalability
- Real-time event processing
- Secure authentication mechanisms
- Efficient video stream processing
- Automated deployments
- Maintainable and modular development practices

# 4. API Contracts
Neighbourhood WatchDog exposes five contract surfaces: the browser REST API, the paired WatchDog Agent control API, real-time WebSockets, MediaMTX WHEP playback, and the MediaMTX publish-authorisation callback. The FastAPI backend owns the REST, WebSocket and callback contracts; the dashboard and native Agent consume them.

### 5.1 Common HTTP conventions

The OpenAPI standard service contract is hosted at this https://api.neighbourhoodwatchdog.co.za/docs

# 6. Deployment

### 7.1 Deployment Requirements
#### Live, Accessible System
Available at: https://neighbourhoodwatchdog.co.za


#### Environment Parity
There are 3 distinct environments:
- Development: Local docker-compose, run manually locally.
- Staging: A single EC2 instance running the full stack via Docker compose deployed automatically by a GitHub Actions workflow triggered on pushes to the `dev` branch
- Production: a separate architecture on AWS:ECS on EC2 for the backend, a standalone EC2 instance for mediamtx (relay for sending the streaming to the client from the edge agent), and RDS for the database. Deployed automatically by a GitHub Actions workflow triggered on every push to the `main` branch.

#### Infrastructure as Code / Containerisation
Infrastructure as code is managed in [__main.py__](../watchdog-infra/__main__.py). All the services are containerised via Docker and deployment is driven by declarative task definitions (with AWS ECS) and Docker Compose files rather than manual console operations.

#### Secrets Management
No credentials are committed to the GitHub repository. Staging generates it .env file at deploy time from the Github Actions secrets. Production uses AWS Secrets Manager which holds all sensitive configuration which is then injected into the different ECS containers via the task definitions `secrets` field.

#### Rollback strategry
The system supports rollback in the following ways:
1. Application rollback (ECS task definitions): Each deploy registers a new immutable task definition rather changing an existing one. So previous versions are still available and can be rolled back to by pointing the service at the last known good revision.
2. Coniguration rollback (Secrets Manager): The Secrets Manager retains prior versions automatically thus allowing rollback.

### Deployment Diagram

![Prod Deployment Diagram](/docs/images/Production%20Deployment%20Diagramv2.svg)

![Staging Deployment Diagram](/docs/images/Staging%20Deployment%20Diagramv3.drawio.svg)

### CI/CD Pipeline Diagram

![CI/CD Pipeline Diagram](/docs/images/CI_CD%20Pipeline%20Diagramv1.drawio.svg)


# 8. NFR Testing

## NFR Traceability Matrix

| NFR ID | Quantified requirement | Design tactic / implementation | Verification test / tool | Target | Actual result | Status |
|---|---|---|---|---:|---|---|
| QR-01 | On the fixed labelled person-detection evaluation harness, human detection precision shall be at least 60% and recall shall be at least 60%. | The person detector uses a confidence threshold of `0.25` and NMS IoU threshold of `0.70`, selected through a 49-candidate tuning search. DeepSORT tracking and `TEMPORAL_CONFIRMATION_FRAMES=3` prevent alerts from being raised from a single unconfirmed frame. | `ai/evaluation/run_baseline.py` executed against the fixed 24-item labelled person-detection harness. Temporal confirmation is verified separately by `ai/tests/test_alert_confirmation.py`. | Precision ≥60%; Recall ≥60% | Precision **96.67%**, recall **96.67%**, F1 **96.67%**; **29 TP, 1 FP, 1 FN**. | Met |

### Availability

| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-02 | ECS recovers killed task to health within 360s | ECS circuit breaker + ASG. Health check threshold is set at 5 x 30s to avoid premature failover on transient blips | Manually run `aws ecs stop-task`, time until ALB target group reports healthy again | < health-check grace period (360s once reverted from the temporary 10s) | 337s |
| QR-03 |  mediamtx stream resumes within 60s of a mediamtx restart | Edge agent RTSP reconnect/retry with backoff | Restart mediamtx container, time until WebRTC stream is viewable again | < 60s | 5.5s (T0 20:58:51Z, readyTime 20:58:56.8Z) |


### Security

| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-04 | Zero high/critical dependancy CVEs on `main` | Automated dependancy scanning in CI | `pip audit` + `npm audit` | 0 high or critical | 0 findings |
| QR-05 | Zero medium+ severity findings on staging | Input validation, security headers, limited exposure | OWASP ZAP baseline scan again staging | 0 medium+ | 0 (There was a false positive critical) |
| QR-04 | 0 secrets committed to the repository | Making use of GitHub Actions secrets and Secrets Manager | `gitleaks` | 0 findings | 0 findings |

### Recoverability 

| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-05 | A failed production deployment can be rolled back to the previous health task definition within 5 minutes | ECS task definition rollback and the deployment circuit breaker | Force a bad deploy and run the documented rollback command and test time until health | <= 5 mins | service never left healthy state because the circuit breaker prevented the bad revision from ever reaching majority healthy status. The broken task auto stopped within seconds. 2 out of 3 good tasks kept serving throughout. |
| QR-06 | Edge agent continues operating in last-known camera config for at least indefinitely if the backend is not reachable | Local caching of the last successful request for the list of enabled cameras | Turn the backend off and on and observe whether the stream continues to be pushed on the list of existing cameras | runs indefinitely | runs indefinitely thanks to caching of camera configurations. And when it does send out requests, it sends them out with exponential backoff so it will not further break the backend if there are issues with it. |

### Scalability

| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-07 | ECS launches an additional task within 3 minutes of sustained CPU and/or memory threshold being exceeded under load | ASG and ECS target-tracking auto-scaling policy | Locust load test sustained past the threshold, watch `describe-services` for scale out event | <= 3 minutes | +-38s (alarm transitioned to ALARM at 19:48:44Z UTC and the earliest observable capacity improvement in Locust data was at 19:49:22Z UTC) |
| QR-08 | p95 latency stays under 2500ms at 500 concurrent virtual users at 300 RPS | Connection pooling + indexing + auto-scaling and Redis caching for selected endpoints | Sustained Locust load test, 500 VUs, 12.5min | p95 < 2500ms at 500 Virtual Users | 2400ms at 500 users at 233-280 RPS |
| QR-9 | Error rate at peak load | Connection pool limit | Locust | <1% | 0.24% |

### Maintainability
| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-10 | SonarQube Maintainability rating of A on code in main branch | Code quality requirements | SonarQube | A rating | A rating |

### Accessibility

| ID | Quantified Requirement | Tactic in SAS | Test / tool | Target | Actual |
|---|---|---|---|---|---|
| QR-10 | Google Lighthouse accessibility score above 95 on production frontend | Code quality requirements | Google Lighthouse | 95 accessibility rating | 95 accessibility rating |