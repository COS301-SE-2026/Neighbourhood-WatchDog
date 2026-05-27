<div align="center">

<br/>

<picture>
  <img src="assets/logo.png" alt="Neighbourhood WatchDog Logo" width="18%"/>
</picture>

<br/><br/>

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=18&pause=1000&color=00B4D8&center=true&vCenter=true&width=700&lines=We+don%27t+just+detect+threats%2C+we+predict+them.;Real-time+AI+surveillance+%C2%B7+YOLOv8+%2B+DeepSORT;Community+safety%2C+powered+by+intelligence." alt="Typing SVG"/>

<br/><br/>

<img src="assets/team_intrepid_logo.png" alt="Team Intrepid" height="60"/>
&nbsp;&nbsp;
<img src="assets/epiuse_logo.png" alt="EPI-USE Africa" height="60"/>
&nbsp;&nbsp;
<img src="assets/up_logo.png" alt="University of Pretoria" height="60"/>

<br/><br/>

[![CI Pipeline](https://img.shields.io/github/actions/workflow/status/COS301-SE-2026/Neighbourhood-WatchDog/ci.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=CI&labelColor=0D1B2A&color=00B4D8)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/actions/workflows/ci.yml)
[![CD Pipeline](https://img.shields.io/badge/CD%20Pipeline-passing-00B4D8?style=for-the-badge&logo=githubactions&logoColor=white&labelColor=0D1B2A)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/actions)
[![Commit Activity](https://img.shields.io/github/commit-activity/m/COS301-SE-2026/Neighbourhood-WatchDog/Dev?style=for-the-badge&logo=git&logoColor=white&label=Commits&labelColor=0D1B2A&color=00B4D8)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/commits/Dev)
[![Open Issues](https://img.shields.io/github/issues-raw/COS301-SE-2026/Neighbourhood-WatchDog?style=for-the-badge&logo=github&logoColor=white&label=Issues&labelColor=0D1B2A&color=0096C7)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/issues)
[![Closed Issues](https://img.shields.io/github/issues-closed-raw/COS301-SE-2026/Neighbourhood-WatchDog?style=for-the-badge&logo=github&logoColor=white&label=Closed&labelColor=0D1B2A&color=023E8A)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/issues?q=is%3Aissue+is%3Aclosed)
[![Status](https://img.shields.io/maintenance/maintained/2026?style=for-the-badge&label=Status&labelColor=0D1B2A&color=00B4D8)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog)

</div>

---

## Table of Contents

<details>
  <summary>Click to expand</summary>

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Demo & Presentation](#demo--presentation)
- [Meet Team Intrepid](#meet-team-intrepid)
- [Technologies Used](#technologies-used)
- [Branching Strategy](#branching-strategy)
- [Contact Us](#contact-us)

</details>

---

## Project Overview

**Neighbourhood WatchDog** is a centralised, AI-assisted security platform designed to strengthen community-based safety efforts across South Africa. Built as a **COS 301 Capstone Project** at the **University of Pretoria**, in partnership with **EPI-USE Africa**.

The system integrates community CCTV infrastructure with real-time AI-driven video analysis to detect suspicious activity and surface actionable alerts to security personnel through a unified monitoring dashboard.

Existing CCTV cameras and alarm systems operate in isolation and respond only **after** an incident has occurred. Neighbourhood WatchDog shifts communities from **incident response** toward **incident prevention** — detecting threats before they escalate, tracking individuals across cameras, and generating predictive risk scores for high-risk zones and time windows.

[![Project Board](https://img.shields.io/badge/Project_Board-GitHub_Projects-00B4D8?style=flat-square&logo=github&logoColor=white&labelColor=0D1B2A)](https://github.com/orgs/COS301-SE-2026/projects/)

---

## System Architecture

The platform consists of six primary subsystems:

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {
  'primaryColor':'#00B4D8', 'primaryTextColor':'#E0F7FA',
  'primaryBorderColor':'#0096C7', 'lineColor':'#90E0EF',
  'secondaryColor':'#0D1B2A','tertiaryColor':'#03045E','background':'#03045E',
  'fontSize':'14px'
}}}%%
flowchart TD
    subgraph VI["Video Ingestion"]
        CAM(["IP Cameras RTSP"])
        MTX(["MediaMTX Relay"])
        FF(["FFmpeg Frame Extractor"])
        KAF(["Apache Kafka"])
    end
    subgraph AI["AI Detection Engine"]
        YOLO(["YOLOv8 Detection"])
        DS(["DeepSORT Tracking"])
        BC(["Behaviour Classifier"])
    end
    subgraph AE["Alert & Event Management"]
        AT(["Alert Threshold Engine"])
        WS(["WebSocket Delivery"])
        S3A(["S3 Footage Archival"])
    end
    subgraph UAC["User & Access Control"]
        COG(["AWS Cognito RBAC + MFA"])
    end
    subgraph MD["Monitoring Dashboard"]
        NEXT(["Next.js Dashboard"])
    end
    subgraph ST["Data & Storage"]
        PG(["PostgreSQL + Row-Level Security"])
        S3B(["S3 Tiered Storage"])
    end
    CAM --> MTX --> FF --> KAF --> YOLO --> DS --> BC
    BC --> AT --> WS --> NEXT
    AT --> S3A --> S3B
    NEXT --> COG
    AT --> PG
    classDef ingestion fill:#03045E,stroke:#00B4D8,color:#E0F7FA
    classDef ai fill:#03045E,stroke:#0096C7,color:#E0F7FA
    classDef alert fill:#03045E,stroke:#48CAE4,color:#E0F7FA
    classDef storage fill:#03045E,stroke:#023E8A,color:#E0F7FA
    classDef ui fill:#03045E,stroke:#90E0EF,color:#E0F7FA
    class CAM,MTX,FF,KAF ingestion
    class YOLO,DS,BC ai
    class AT,WS,S3A alert
    class PG,S3B storage
    class NEXT,COG ui
```

| Subsystem | Description |
|:---|:---|
| **Video Ingestion** | Accepts RTSP streams from IP cameras via MediaMTX relay; extracts frames via FFmpeg and publishes to Kafka |
| **AI Detection Engine** | YOLOv8 + DeepSORT pipeline for human presence detection, behaviour classification, and multi-camera tracking |
| **Alert & Event Management** | Threshold-based alert triggering, real-time WebSocket delivery, footage archival to S3 |
| **User & Access Control** | AWS Cognito RBAC with four roles, MFA for admins, neighbourhood-level data isolation |
| **Monitoring Dashboard** | Next.js real-time dashboard with live alert feed, camera status, stream preview, and incident history |
| **Data & Storage** | Tiered S3 storage (hot/cold), configurable retention policies, PostgreSQL row-level security |

---

## Features

<div align="center">

<table width="100%">
  <tr>
    <td width="33%" valign="top">
      <h3 align="center">Core Features</h3>
      <ul>
        <li>Live RTSP camera stream ingestion via MediaMTX</li>
        <li>Real-time human presence detection (YOLOv8)</li>
        <li>Threshold-based alert generation with WebSocket delivery</li>
        <li>Monitoring dashboard with live alert feed</li>
        <li>Role-based access control (4 roles)</li>
        <li>Incident history with S3 clip retrieval</li>
        <li>MFA enforcement for admins via AWS Cognito</li>
        <li>Neighbourhood-level data isolation</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3 align="center">Advanced Features</h3>
      <ul>
        <li>Loitering and perimeter scanning classification</li>
        <li>Multi-camera individual tracking via DeepSORT</li>
        <li>After-hours intrusion detection</li>
        <li>External notifications: Email, WhatsApp, Discord</li>
      </ul>
    </td>
    <td width="33%" valign="top">
      <h3 align="center">Wow Factors</h3>
      <ul>
        <li>Predictive neighbourhood risk scoring engine</li>
        <li>Alert frequency and incident trend analytics</li>
        <li>Autonomous patrol assistance with movement path summaries</li>
      </ul>
    </td>
  </tr>
</table>

</div>

---

## Getting Started

### Prerequisites

<div align="center">

[![Docker](https://img.shields.io/badge/Docker-required-00B4D8?style=flat-square&logo=docker&logoColor=white&labelColor=0D1B2A)](https://www.docker.com/)
[![Node.js](https://img.shields.io/badge/Node.js-v18+-00B4D8?style=flat-square&logo=nodedotjs&logoColor=white&labelColor=0D1B2A)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-00B4D8?style=flat-square&logo=python&logoColor=white&labelColor=0D1B2A)](https://www.python.org/)
[![AWS CLI](https://img.shields.io/badge/AWS_CLI-required-0096C7?style=flat-square&logo=amazonaws&logoColor=white&labelColor=0D1B2A)](https://aws.amazon.com/cli/)
[![Git](https://img.shields.io/badge/Git-required-0096C7?style=flat-square&logo=git&logoColor=white&labelColor=0D1B2A)](https://git-scm.com/)

</div>

### Installation

<details open>
<summary><strong>1. Clone the repository</strong></summary>
<br>

```bash
git clone https://github.com/COS301-SE-2026/Neighbourhood-WatchDog.git
cd Neighbourhood-WatchDog
```

</details>

<details>
<summary><strong>2. Configure environment variables</strong></summary>
<br>

```bash
cp .env.example .env
# Fill in your AWS, Cognito, and database credentials in .env
```

</details>

<details>
<summary><strong>3. Start all services with Docker Compose</strong></summary>
<br>

```bash
docker compose up --build
```

</details>

### Access

| Service | URL |
|:---|:---|
| Dashboard | `http://localhost:3000` |
| API | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |

---

## Project Structure

```
Neighbourhood-WatchDog/
│
├── frontend/          # Next.js dashboard (React, TailwindCSS, HLS.js)
├── backend/           # FastAPI backend (REST API, WebSocket, Celery)
├── ai/                # AI pipeline (YOLOv8, DeepSORT, OpenCV)
├── infra/             # Docker, docker-compose, AWS configuration
├── docs/              # Project documentation
└── assets/            # Logos, images, README assets
```

---

## Documentation

<div align="center">

[![SRS](https://img.shields.io/badge/Software_Requirements_Spec-View-00B4D8?style=for-the-badge&logo=googledocs&logoColor=white&labelColor=0D1B2A)](docs/srs.md)


</div>

> Documentation links will be updated after each demo.

---

## Demo & Presentation

<div align="center">

| Demo | Slides | Video |
|:---:|:---:|:---:|
| Demo 1 | [![Slides](https://img.shields.io/badge/Slides_1-View-00B4D8?style=flat-square&logo=googleslides&logoColor=white&labelColor=0D1B2A)](#) | [![Video](https://img.shields.io/badge/Video_1-Watch-00B4D8?style=flat-square&logo=youtube&logoColor=white&labelColor=0D1B2A)](docs/Demo1%20Video.mov) |
| Demo 2 | [![Slides](https://img.shields.io/badge/Slides_2-View-0096C7?style=flat-square&logo=googleslides&logoColor=white&labelColor=0D1B2A)](#) | [![Video](https://img.shields.io/badge/Video_2-Watch-0096C7?style=flat-square&logo=youtube&logoColor=white&labelColor=0D1B2A)](#) |
| Demo 3 | [![Slides](https://img.shields.io/badge/Slides_3-View-023E8A?style=flat-square&logo=googleslides&logoColor=white&labelColor=0D1B2A)](#) | [![Video](https://img.shields.io/badge/Video_3-Watch-023E8A?style=flat-square&logo=youtube&logoColor=white&labelColor=0D1B2A)](#) |
| Demo 4 | [![Slides](https://img.shields.io/badge/Slides_4-View-03045E?style=flat-square&logo=googleslides&logoColor=white&labelColor=0D1B2A)](#) | [![Video](https://img.shields.io/badge/Video_4-Watch-03045E?style=flat-square&logo=youtube&logoColor=white&labelColor=0D1B2A)](#) |

</div>

---

## Meet Team Intrepid

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=500&size=14&pause=1000&color=90E0EF&center=true&vCenter=true&width=700&lines=Five+engineers+%C2%B7+One+mission+%C2%B7+Safer+communities" alt="Team tagline"/>

<br/><br/>

<table width="100%">
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/">
        <img src="https://github.com/ghost.png?size=120" width="90" style="border-radius:50%" alt="Jared Williams"/>
      </a>
      <br/><br/>
      <b>Jared Williams</b><br/>
      <sub><code>u24581039</code></sub><br/><br/>
      <img src="https://img.shields.io/badge/Team%20Lead-00B4D8?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/>
      <img src="https://img.shields.io/badge/Full--Stack%20Dev-0096C7?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/><br/>
      <sub>Python · FastAPI · React · Next.js · PostgreSQL · Docker</sub><br/><br/>
      <a href="https://github.com/"><img src="https://img.shields.io/badge/-GitHub-0D1B2A?style=flat-square&logo=github&logoColor=white"/></a>
      <a href="https://www.linkedin.com/in/jared-williams-5286a6283/"><img src="https://img.shields.io/badge/-LinkedIn-00B4D8?style=flat-square&logo=linkedin&logoColor=white&labelColor=0D1B2A"/></a>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/">
        <img src="https://github.com/ghost.png?size=120" width="90" style="border-radius:50%" alt="Ange Yehouessi"/>
      </a>
      <br/><br/>
      <b>Ange Yehouessi</b><br/>
      <sub><code>u24614484</code></sub><br/><br/>
      <img src="https://img.shields.io/badge/Backend%20Engineer-00B4D8?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/><br/>
      <sub>Python · FastAPI · Node.js · PostgreSQL · REST API</sub><br/><br/>
      <a href="https://github.com/"><img src="https://img.shields.io/badge/-GitHub-0D1B2A?style=flat-square&logo=github&logoColor=white"/></a>
      <a href="https://www.linkedin.com/in/ange-yehouessi-624086376/"><img src="https://img.shields.io/badge/-LinkedIn-00B4D8?style=flat-square&logo=linkedin&logoColor=white&labelColor=0D1B2A"/></a>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/">
        <img src="https://github.com/ghost.png?size=120" width="90" style="border-radius:50%" alt="Joshua Mahabeer"/>
      </a>
      <br/><br/>
      <b>Joshua Mahabeer</b><br/>
      <sub><code>u24597092</code></sub><br/><br/>
      <img src="https://img.shields.io/badge/AI%2FML%20Engineer-00B4D8?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/><br/>
      <sub>Python · OpenCV · YOLOv8 · React · Docker · C++</sub><br/><br/>
      <a href="https://github.com/"><img src="https://img.shields.io/badge/-GitHub-0D1B2A?style=flat-square&logo=github&logoColor=white"/></a>
      <a href="https://www.linkedin.com/in/joshua-mahabeer-286528269/"><img src="https://img.shields.io/badge/-LinkedIn-00B4D8?style=flat-square&logo=linkedin&logoColor=white&labelColor=0D1B2A"/></a>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/">
        <img src="https://github.com/ghost.png?size=120" width="90" style="border-radius:50%" alt="Obed Edom Mbaya"/>
      </a>
      <br/><br/>
      <b>Obed Edom Mbaya</b><br/>
      <sub><code>u24595889</code></sub><br/><br/>
      <img src="https://img.shields.io/badge/AI%2FML%20Engineer-00B4D8?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/><br/>
      <sub>Python · FastAPI · LangGraph · Next.js · PostgreSQL · Docker</sub><br/><br/>
      <a href="https://github.com/"><img src="https://img.shields.io/badge/-GitHub-0D1B2A?style=flat-square&logo=github&logoColor=white"/></a>
      <a href="https://www.linkedin.com/in/obed-edom-mbaya-01197423b/"><img src="https://img.shields.io/badge/-LinkedIn-00B4D8?style=flat-square&logo=linkedin&logoColor=white&labelColor=0D1B2A"/></a>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/">
        <img src="https://github.com/ghost.png?size=120" width="90" style="border-radius:50%" alt="Zaman Bassa"/>
      </a>
      <br/><br/>
      <b>Zaman Bassa</b><br/>
      <sub><code>u24744931</code></sub><br/><br/>
      <img src="https://img.shields.io/badge/DevOps%20Engineer-00B4D8?style=flat-square&logoColor=white&labelColor=0D1B2A"/><br/><br/>
      <sub>TypeScript · Python · Docker · PostgreSQL · GitHub Actions</sub><br/><br/>
      <a href="https://github.com/"><img src="https://img.shields.io/badge/-GitHub-0D1B2A?style=flat-square&logo=github&logoColor=white"/></a>
      <a href="https://www.linkedin.com/in/zaman-bassa-033673360/"><img src="https://img.shields.io/badge/-LinkedIn-00B4D8?style=flat-square&logo=linkedin&logoColor=white&labelColor=0D1B2A"/></a>
    </td>
  </tr>
</table>

</div>

---

## Technologies Used

<div align="center">

<img src="https://skillicons.dev/icons?i=nextjs,react,ts,tailwind,python,fastapi,opencv,pytorch,docker,postgres,aws,githubactions&perline=12" alt="Tech stack icons"/>

</div>

<br/>

<details>
<summary><strong>Frontend</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white) | React-based dashboard framework with SSR |
| ![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB) | Component-based UI library |
| ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white) | Static typing across the frontend |
| ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white) | Utility-first styling framework |
| HLS.js | Live stream playback in browser |

</details>

<details>
<summary><strong>Backend</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | REST API and WebSocket server |
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | Primary backend language |
| ![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logoColor=white) | Distributed task queue |
| ![Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white) | Frame event streaming pipeline |
| WebSocket | Real-time alert push delivery |

</details>

<details>
<summary><strong>AI / ML Pipeline</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![YOLOv8](https://img.shields.io/badge/YOLOv8-00FFFF?style=flat-square&logoColor=black) | Real-time human detection |
| ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white) | Frame preprocessing and video I/O |
| ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white) | Model inference backend |
| DeepSORT | Multi-camera individual tracking |

</details>

<details>
<summary><strong>Video Ingestion</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=flat-square&logo=ffmpeg&logoColor=white) | Frame extraction from RTSP streams |
| MediaMTX | RTSP relay and stream management |

</details>

<details>
<summary><strong>Database & Storage</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white) | Primary relational database with row-level security |
| ![Amazon RDS](https://img.shields.io/badge/Amazon_RDS-527FFF?style=flat-square&logo=amazonrds&logoColor=white) | Managed PostgreSQL hosting |
| ![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?style=flat-square&logo=amazons3&logoColor=white) | Tiered video clip archival |

</details>

<details>
<summary><strong>DevOps & Cloud</strong></summary>
<br/>

| Technology | Purpose |
|:---|:---|
| ![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=amazonaws&logoColor=white) | Cloud infrastructure provider |
| ![EC2](https://img.shields.io/badge/Amazon_EC2-FF9900?style=flat-square&logo=amazonec2&logoColor=white) | Compute instances |
| ![Cognito](https://img.shields.io/badge/Amazon_Cognito-DD344C?style=flat-square&logo=amazoncognito&logoColor=white) | Auth, RBAC, and MFA |
| ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) | Service containerisation |
| ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white) | CI/CD pipelines |
| ![CloudWatch](https://img.shields.io/badge/Amazon_CloudWatch-FF4F8B?style=flat-square&logo=amazoncloudwatch&logoColor=white) | Observability and logging |

</details>

---

## Branching Strategy

This project follows a **Git Flow** branching strategy:

```mermaid
%%{init: {'theme':'dark', 'themeVariables': {
  'primaryColor':'#00B4D8','primaryTextColor':'#E0F7FA',
  'primaryBorderColor':'#0096C7','lineColor':'#90E0EF',
  'secondaryColor':'#0D1B2A','tertiaryColor':'#03045E','background':'#03045E'
}}}%%
flowchart LR
    main(["main"]):::main
    dev(["dev"]):::dev
    feat(["feature/name"]):::feat
    fix(["fix/name"]):::fix
    main --> dev
    dev --> feat
    dev --> fix
    feat -->|PR + review| dev
    fix -->|PR + review| dev
    dev -->|release| main
    classDef main fill:#03045E,color:#E0F7FA,stroke:#00B4D8
    classDef dev  fill:#023E8A,color:#E0F7FA,stroke:#0096C7
    classDef feat fill:#0077B6,color:#E0F7FA,stroke:#48CAE4
    classDef fix  fill:#0096C7,color:#E0F7FA,stroke:#90E0EF
```

| Branch | Purpose |
|:---|:---|
| `main` | Production-ready releases only |
| `dev` | Integration branch — all features merge here first |
| `feature/<name>` | Individual feature branches, branched from `dev` |
| `fix/<name>` | Bug fix branches, branched from `dev` |

All pull requests require at least **one peer review** before merging into `dev`. Direct commits to `main` are not permitted.

---

## Contact Us

<div align="center">

Have questions, ideas, or want to get in touch?

[![Email](https://img.shields.io/badge/intrepid.capstone%40gmail.com-Contact_Us-00B4D8?style=for-the-badge&logo=gmail&logoColor=white&labelColor=0D1B2A)](mailto:intrepid.capstone@gmail.com)

<br/><br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=00B4D8&height=120&section=footer" width="100%"/>

<sub><i>COS 301 Capstone Project 2026 · University of Pretoria · EPI-USE Africa · Team Intrepid</i></sub>

</div>
