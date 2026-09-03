# Software Architecture Specification (SAS)
# Neighbourhood WatchDog

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
![Architecture Diagramv2](/docs/images/Architecture%20Diagramv2.drawio.svg)

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

### 7.1 Common HTTP conventions

The OpenAPI standard service contract is hosted at this https://api.neighbourhoodwatchdog.co.za/docs

# 8. Deployment

### 8.1 Deployment Requirements
#### Live, Accessible System
Available at: https://neighbourhoodwatchdog.co.za


#### Environment Parity
There are 3 distinct environments:
- Development: Local docker-compose, run manually locally.
- Staging: A single EC2 instance running the full stack via Docker compose deployed automatically by a GitHub Actions workflow triggered on pushes to the `dev` branch
- Production: a separate architecture on AWS:ECS on EC2 for the backend, a standalone EC2 instance for mediamtx (relay for sending the streaming to the client from the edge agent), and RDS for the database. Deployed automatically by a GitHub Actions workflow triggered on every push to the `main` branch.

#### Infrastructure as Code / Containerisation
All the services are containerised via Docker and deployment is driven by declarative task definitions (with AWS ECS) and Docker Compose files rather than manual console operations.

#### Secrets Management
No credentials are committed to the GitHub repository. Staging generates it .env file at deploy time from the Github Actions secrets. Production uses AWS Secrets Manager which holds all sensitive configuration which is then injected into the different ECS containers via the task definitions `secrets` field.

#### Rollback strategry

### Deployment Diagram

![Prod Deployment Diagram](/docs/images/Prod%20Deployment%20Diagramv1.drawio.svg)

![Staging Deployment Diagram](/docs/images/Prod%20Deployment%20Diagramv1.drawio.svg)

### CI/CD Pipeline Diagram

![CI/CD Pipeline Diagram](/docs/images/CI_CD%20Pipeline%20Diagramv1.drawio.svg)