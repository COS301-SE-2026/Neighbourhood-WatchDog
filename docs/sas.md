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
| Strategy | The AI detection worker can delegate frame analysis to a selected detection strategy. The current implementation uses YOLO-based person detection with DeepSORT tracking. Future strategies can support vehicle, weapon, fall, loitering, or perimeter-intrusion detection without changing the camera runtime’s overall workflow. |
| Observer | When an AI worker posts a detection or annotation to the FastAPI backend, the backend broadcasts alert and annotation updates through WebSockets. Dashboard clients subscribed through WebSocket connections receive updates immediately and refresh alerts or bounding-box overlays without polling. |
| State | The camera playback UI moves between distinct states: connecting, live, and unavailable/offline. When a user selects a camera, the frontend initiates WHEP/WebRTC playback and displays the appropriate state based on connection success, stream availability, or failure. Closing the camera view ends the playback session and returns the component to its initial state. |
| Factory | A factory can centralise creation of camera-specific runtime components. Given a camera configuration, it would construct the corresponding FFmpeg publisher, AI detection worker, credentials, stream path, and process configuration. |
| Chain of Responsibility | Requests pass through sequential validation and authorisation stages: authentication, role/property access checks, request validation, internal-agent token validation, and finally route/service execution. FastAPI middleware and dependency functions naturally support this pattern. |
| Command | Camera actions such as enable, disable, start publisher, stop publisher, start detection, and stop detection, can be represented as commands. This would make operations easier to queue, retry, log, audit, and potentially execute remotely through the WatchDog Agent. |

### 2.3 Architectural Constraints
- Existing CCTV and IP cameras must provide RTSP streams.
- Real-time video processing must minimize latency while supporting multiple concurrent streams.
- Sensitive information must remain encrypted during transmission.
- Secrets and credentials may not be committed to source control.
- All deployments must be reproducible using Infrastructure as Code and containerization technologies.
- The system must support independent scaling of AI processing services.
- Production deployments must remain accessible through public URLs.
- Services must support horizontal scalability where appropriate.

### 2.4 Architectural Diagram


### 2.5 Mapping Quality Requirements to Architectural Decisions


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

All REST requests and responses use `application/json` unless a media-specific contract says otherwise.

- **Browser authentication:** protected browser routes resolve the caller from the Cognito/JWT-backed user context. Controller-level role checks enforce resident, property-administrator, neighbourhood-administrator and system-administrator permissions.
- **Agent authentication:** Agent runtime endpoints use a paired edge-Agent credential; detection ingestion currently requires `X-Internal-Token`.
- **Identifiers:** resource identifiers are UUIDs unless stated otherwise.
- **Success responses:** current endpoints are not yet fully normalised. Some return `{ "status", "message", "data" }`, some return a schema object, and deletion endpoints return `204 No Content`.
- **Error responses:** the current FastAPI implementation returns `{ "detail": "…" }` for many failures and the standard FastAPI `422` validation format. A unified public error envelope is **Planned**.

Recommended future error envelope:

```json
{
  "error": "forbidden",
  "cause": "The current user is not allowed to edit this camera.",
  "suggestion": "Ask a property or neighbourhood administrator to perform this action.",
  "request_id": "correlation-id"
}
```

### 7.2 Browser REST API

The following routes cover the principal Demo 2 browser flows. Request and response fields are defined by the Pydantic schemas in `backend/app/schemas/`, which remain the field-level source of truth.

| Method | Path | Auth / role | Purpose | Realises |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | No | Returns `{ "status": "ok" }` for deployment smoke checks. | Operational health |
| `POST` | `/auth/signup` | No | Register a user from the sign-up request schema. Rate limited to 3/minute. | R7.1.1 |
| `POST` | `/auth/confirm` | No | Confirm account registration with a confirmation code. | R7.1.2 |
| `POST` | `/auth/login` | No | Authenticate a registered user. Rate limited to 5/minute. | R7.5.1 |
| `POST` | `/auth/resend-code` | No | Re-send an account-confirmation code. | R7.1.2 |
| `GET` | `/auth/me` | User | Return the current authenticated user's profile. | R4, R7.5.1 |
| `POST` | `/auth/logout` | User | End the browser-side session workflow. | R7.5.2 |
| `POST` | `/neighbourhood/create-neighbourhood` | Resident | Create a neighbourhood using name, location and initial property context. | R7.2 |
| `POST` | `/neighbourhood/join` | User | Submit a join request using a neighbourhood join code. | R7.3.1–R7.3.3 |
| `GET` | `/neighbourhood/join-requests` | User | List join requests visible in the caller's administrative context. | R7.3.4 |
| `PATCH` | `/neighbourhood/join-requests/{request_id}` | Neighbourhood administrator | Approve or deny a join request using `{ "action": "…" }`. | R7.3.4 |
| `POST` | `/properties/create-property` | Resident | Create a property using its address and type. | R8.1.1 |
| `GET` | `/properties/my-properties` | Resident | List the caller's properties. | R8 |
| `GET` | `/properties/{property_id}` | Resident | Fetch property details, including related users, neighbourhood and cameras. | R8, R8.4 |
| `POST` | `/camera/register-camera` | Resident | Register a camera and associate it with the caller's property. | R7.4.1, R8.4 |
| `GET` | `/camera/property/{property_id}` | Resident | List cameras belonging to a property. | R5.3, R7.4 |
| `PATCH` | `/camera/{camera_id}` | Resident | Update camera details, including its enabled state. | R7.4.2 |
| `DELETE` | `/camera/{camera_id}` | Resident | Permanently deregister a camera. Returns `204`. | R7.4.2.3 |
| `GET` | `/cameras/{camera_id}/settings` | Neighbourhood/property/system administrator | Retrieve the confidence threshold and detection zones. | R5.5.2–R5.5.3 |
| `PATCH` | `/cameras/{camera_id}/settings` | Neighbourhood/property/system administrator | Update `{ "confidence_threshold": number }`. | R2.2.2, R5.5.3 |
| `POST` | `/cameras/{camera_id}/zones` | Neighbourhood/property/system administrator | Create a named polygon detection zone. | R2.1.1, R5.5.2 |
| `DELETE` | `/cameras/{camera_id}/zones/{zone_id}` | Neighbourhood/property/system administrator | Remove a detection zone. Returns `204`. | R5.5.2 |
| `GET` | `/alerts/{neighbourhood_id}` | Authorised user | List alerts using optional status, camera, detection type, date and pagination filters. | R3.1, R3.2, R5.1, R5.4 |
| `PATCH` | `/alerts/{alert_id}/acknowledge` | Authorised user | Acknowledge an alert and return its updated state. | R5.1.3–R5.1.4 |
| `GET` | `/audit/get-audit-logs` | System administrator | Retrieve paginated and filterable audit records. | R4.4.1 |

**Browser safety rule:** a browser-facing response must not disclose a source-camera RTSP URL, Agent API key, internal token or MediaMTX publisher password.

### 7.3 Paired WatchDog Agent control API

The native Agent calls this surface during first-time pairing and when reconciling the active camera runtime. Its credential is retained in the operating-system keyring, not in browser-accessible storage.

| Method | Path | Caller / authentication | Purpose | Realises |
| --- | --- | --- | --- | --- |
| `GET` | `/pairing-token/{property_id}` | Resident | Issue a pairing token for the selected property. The pairing service is responsible for expiry and one-time validation. | R1.1.4, R7.4.1.3 |
| `GET` | `/pairing-token/token/{pairing_token}` | Native Agent during setup | Exchange a valid pairing token for a property-scoped Agent credential. | R1.1.4, R4.1.6 |
| `GET` | `/internal/cameras/enabled` | Paired Agent credential | Return only enabled cameras for the Agent's property: camera ID, Agent-only RTSP URL, neighbourhood ID, threshold and per-camera MediaMTX publisher credentials. | R1.1.3–R1.4.2, R2.1.4 |
| `POST` | `/internal/detections` | `X-Internal-Token` | Persist a validated detection result; a qualifying event can create an alert. Returns `201`. Must be network-restricted in production. | R2.1.3–R2.2.3, R3.1 |
| `POST` | `/api/stream/cameras/{camera_id}/annotations` | Paired Agent credential | Broadcast current annotation/track data to connected dashboard clients. Returns `{ "status": "broadcasted" }`. | R2.1.4–R2.1.5, R5.3 |

### 7.4 Real-time WebSocket contracts

The current implementation provides two server-to-browser JSON channels. Both emit `{ "event": "ping" }` after 30 seconds without a received client frame to preserve connection health.

#### Camera annotation channel — `/api/stream/cameras/{camera_id}/annotations/ws`

```json
{
  "camera_id": "camera-uuid",
  "event": "annotation",
  "tracks": [
    {
      "track_id": 17,
      "bbox": [84, 26, 201, 317],
      "detection_type": "person",
      "confidence": 0.91
    }
  ]
}
```

| Direction | Event / payload | Cadence | Realises |
| --- | --- | --- | --- |
| Server → Browser | `{ "camera_id", "event": "annotation", "tracks": [...] }` | Whenever the Agent posts an annotation payload | R2.1, R2.4.1, R5.3 |
| Server → Browser | `{ "event": "ping" }` | 30 seconds of idle receive time | Connection health |
| Browser → Server | Any text frame / heartbeat | Keeps the current session alive; no browser command message is defined. | Connection health |

The browser renders a detection overlay using `bbox`, `detection_type`, `confidence` and optional tracking data. This Agent-originated payload should be promoted to a Pydantic schema before production.

#### Neighbourhood alert channel — `/alerts/{neighbourhood_id}/ws?token={token}`

```json
{
  "event": "new_alert",
  "camera_id": "camera-uuid",
  "detection_type": "HUMAN_PRESENCE",
  "confidence": 0.91
}
```

| Direction | Event / payload | Cadence | Realises |
| --- | --- | --- | --- |
| Server → Browser | `{ "event": "new_alert", "camera_id", "detection_type", "confidence", ... }` | When an alert is broadcast to a neighbourhood | R3.1, R5.1.1 |
| Server → Browser | `{ "event": "ping" }` | 30 seconds of idle receive time | Connection health |
| Browser → Server | Any text frame / heartbeat | No client command discriminator exists; acknowledgement is the REST `PATCH /alerts/{alert_id}/acknowledge` call. | R5.1.3 |

> **Security status — In progress:** the alert WebSocket accepts a `token` query parameter but does not yet validate it, and the annotation WebSocket has no visible user authorisation check. Before production, both handshakes must authenticate the user and enforce the same camera/neighbourhood access policy as the REST API.

### 7.5 Media relay and playback contracts

#### MediaMTX publish-authorisation callback — `POST /internal/mediamtx/auth`

MediaMTX calls the backend before accepting a publisher. It submits a JSON object containing `user`, `password`, `action`, `path`, `protocol`, `ip`, `id` and `query`.

| Caller | Accepted operation | Contract | Result |
| --- | --- | --- | --- |
| MediaMTX | `publish` | Path must match `cameras/<camera-uuid>`. The camera must exist and be enabled. Username is `camera-<camera-uuid>` and password is the HMAC-derived per-camera password. | `204 No Content` when authorised; `401` for invalid camera/path/credential; `403` for unsupported action. |
| MediaMTX | `read` or `playback` | The current callback permits these actions directly. Browser-side stream authorisation remains an **in-progress security requirement**. | `204 No Content` |

#### Browser WHEP/WebRTC playback — `POST {NEXT_PUBLIC_MEDIAMTX_WEBRTC_URL}/cameras/{camera_id}/whep`

Playback begins only after explicit camera selection. The dashboard creates a receive-only WebRTC offer and posts its SDP to MediaMTX:

```http
POST /cameras/{camera_id}/whep
Content-Type: application/sdp

<browser WebRTC offer SDP>
```

MediaMTX returns an SDP answer and may include a `Location` header for the WHEP session resource. On camera-modal close, the dashboard closes the peer connection and sends `DELETE` to that session URL when supplied.

| Direction | Contract | Dashboard state | Realises |
| --- | --- | --- | --- |
| Browser → MediaMTX | `POST` receive-only SDP offer | `connecting` | R1.2.4, R5.3 |
| MediaMTX → Browser | SDP answer and WebRTC media tracks | `live` | R1.2.4, R5.3 |
| Browser → MediaMTX | `DELETE` WHEP session on component unmount, when supplied | `idle` | R1.2.4 |
| Failure | Non-2xx WHEP response or failed peer connection | `unavailable` | R5.2.1 |

### 7.6 Contract ownership and source of truth

| Surface | Owner | Authoritative implementation source | Status |
| --- | --- | --- | --- |
| Browser REST | FastAPI backend | `backend/app/api/controllers/` and `backend/app/schemas/` | Implemented; path naming is not yet normalised |
| Agent control | FastAPI backend and native Agent | `internal_cameras.py`, `detection.py`, `stream.py`, `pairing_token.py` and Agent runtime modules | Implemented; internal network hardening is in progress |
| Real-time WebSockets | FastAPI backend and dashboard | `alert.py`, `stream.py` and frontend WebSocket hooks | Implemented; authentication/authorisation is in progress |
| WHEP/WebRTC | MediaMTX and `CameraFeed.tsx` | MediaMTX WHEP contract and browser implementation | Implemented; staging route/origins require validation |
| Publish authorisation | FastAPI backend and MediaMTX | `internal_cameras.py` and MediaMTX configuration | Implemented for publishing; read/playback policy is in progress |

The generated OpenAPI document is the field-level REST schema source when debug documentation is enabled. Before a production release, the team should publish a controlled OpenAPI artifact in CI or commit a versioned static OpenAPI file rather than enabling debug endpoints publicly.
