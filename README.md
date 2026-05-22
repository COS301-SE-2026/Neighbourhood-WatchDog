<div align="center">


<br/>

<img src="assets/logo.png" alt="Neighbourhood WatchDog Logo" width="20%"/>

<br/>

# Neighbourhood WatchDog

### *We don't just detect threats, we predict them.*

<br/>

<img src="assets/team_intrepid_logo.png" alt="Team Intrepid" height="70" style="margin-right: 16px;"/>
&nbsp;&nbsp;
<img src="assets/epiuse_logo.png" alt="EPI-USE Africa" height="70" style="margin-right: 16px;"/>
&nbsp;&nbsp;
<img src="assets/up_logo.png" alt="University of Pretoria" height="70"/>

<br/><br/>

<p align="center">
  <a href="https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/actions/workflows/ci.yml">
    <img src="https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/actions/workflows/ci.yml/badge.svg" alt="CI Pipeline"/>
  </a>
  <a href="https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/actions">
    <img src="https://img.shields.io/badge/CD%20Pipeline-blue?logo=githubactions&logoColor=white" alt="CD Pipeline"/>
  </a>
</p>

[![Commit Activity](https://img.shields.io/github/commit-activity/m/COS301-SE-2026/Neighbourhood-WatchDog/Dev)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/commits/Dev)
[![Open Issues](https://img.shields.io/github/issues-raw/COS301-SE-2026/Neighbourhood-WatchDog?color=blue)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/issues)
[![Closed Issues](https://img.shields.io/github/issues-closed-raw/COS301-SE-2026/Neighbourhood-WatchDog?color=blue)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog/issues?q=is%3Aissue+is%3Aclosed)
[![Status](https://img.shields.io/maintenance/maintained/2026?label=Status)](https://github.com/COS301-SE-2026/Neighbourhood-WatchDog)

</div>

---

## Table of Contents

<details>
  <summary>Click to expand</summary>

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Demo & Presentation](#-demo--presentation)
- [Meet Team Intrepid](#-meet-team-intrepid)
- [Technologies Used](#-technologies-used)
- [Branching Strategy](#-branching-strategy)
- [Contact Us](#-contact-us)

</details>

---

## Project Overview

**Neighbourhood WatchDog** is a centralised, AI-assisted security platform designed to strengthen community-based safety efforts across South Africa. Built as a **COS 301 Capstone Project** at the **University of Pretoria**, in partnership with **EPI-USE Africa**.

The system integrates community CCTV infrastructure with real-time AI-driven video analysis to detect suspicious activity and surface actionable alerts to security personnel through a unified monitoring dashboard.

Existing CCTV cameras and alarm systems operate in isolation and respond only **after** an incident has occurred. Neighbourhood WatchDog shifts communities from **incident response** toward **incident prevention** — detecting threats before they escalate, tracking individuals across cameras, and generating predictive risk scores for high-risk zones and time windows.

[View Project Board](https://github.com/orgs/COS301-SE-2026/projects/)

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## System Architecture

<!-- TODO: Export architecture diagram as PNG and place in assets/architecture.png -->
<div align="center">
  <img src="docs/images/Architecture Diagram.drawio.svg" alt="System Architecture Diagram" width="50%"/>
</div>

The platform consists of six primary subsystems:

| Subsystem | Description |
|---|---|
| **Video Ingestion** | Accepts RTSP streams from IP cameras via MediaMTX relay; extracts frames via FFmpeg and publishes to Kafka |
| **AI Detection Engine** | YOLOv8 + DeepSORT pipeline for human presence detection, behaviour classification, and multi-camera tracking |
| **Alert & Event Management** | Threshold-based alert triggering, real-time WebSocket delivery, footage archival to S3 |
| **User & Access Control** | AWS Cognito RBAC with four roles, MFA for admins, neighbourhood-level data isolation |
| **Monitoring Dashboard** | Next.js real-time dashboard with live alert feed, camera status, stream preview, and incident history |
| **Data & Storage** | Tiered S3 storage (hot/cold), configurable retention policies, PostgreSQL row-level security |

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Features

**Core Features**
- Live RTSP camera stream ingestion and relay via MediaMTX
- Real-time human presence detection using YOLOv8
- Threshold-based alert generation with WebSocket delivery
- Monitoring dashboard with live alert feed and camera status
- Role-based access control (System Admin, Neighbourhood Admin, Security Officer, Resident)
- Incident history with footage clip retrieval from S3
- MFA enforcement for admin roles via AWS Cognito
- Neighbourhood-level data isolation

**Advanced Features**
- Loitering and perimeter scanning behaviour classification
- Multi-camera individual tracking via DeepSORT
- After-hours intrusion detection
- External notifications via Email, WhatsApp, and Discord

**Wow Factors**
- Predictive neighbourhood risk scoring engine
- Alert frequency and incident trend analytics
- Autonomous patrol assistance with movement path summaries

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.11+)
- [AWS CLI](https://aws.amazon.com/cli/) (configured with credentials)
- [Git](https://git-scm.com/)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/COS301-SE-2026/Neighbourhood-WatchDog.git
cd Neighbourhood-WatchDog

# 2. Copy environment variables
cp .env.example .env
# Fill in your AWS, Cognito, and database credentials in .env

# 3. Start all services with Docker Compose
docker compose up --build
```

### Access

| Service | URL |
|---|---|
| Dashboard | `http://localhost:3000` |
| API | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

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

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Documentation

| Document | Link |
|---|---|
| Software Requirements Specification | [View](#) |
| Architectural Requirements | [View](#) |
| Service Contracts | [View](#) |
| User Manual | [View](#) |
| Technical Installation Manual | [View](#) |
| Coding Standards | [View](#) |

> Documentation links will be updated after each demo.

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Demo & Presentation

| Demo | Slides | Video |
|---|---|---|
| Demo 1 | [Slides 1](#) | [Video 1](#) |
| Demo 2 | [Slides 2](#) | [Video 2](#) |
| Demo 3 | [Slides 3](#) | [Video 3](#) |
| Demo 4 | [Slides 4](#) | [Video 4](#) |

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Meet Team Intrepid

<!-- TODO: Add circular profile photos to assets/team/ for each member -->

| | Name | Student No. | Role | Skills | GitHub | LinkedIn |
|---|---|---|---|---|---|---|
**Jared Williams** | u24581039 | Team Lead & Full-Stack Developer | Python, FastAPI, React, Next.js, PostgreSQL, Docker | [![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github)](https://github.com/) | [![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/jared-williams-5286a6283/) |
**Ange Yehouessi** | u24614484 | Backend Engineer | Python, FastAPI, Node.js, PostgreSQL, REST API | [![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github)](https://github.com/) | [![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/ange-yehouessi-624086376/) |
**Joshua Mahabeer** | u24597092 | AI/ML Engineer | Python, OpenCV, YOLOv8, React, Docker, C++ | [![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github)](https://github.com/) | [![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/joshua-mahabeer-286528269/) |
**Obed Edom Mbaya** | u24595889 | AI/ML Engineer | Python, FastAPI, LangGraph, Next.js, PostgreSQL, Docker | [![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github)](https://github.com/) | [![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/obed-edom-mbaya-01197423b/) |
**Zaman Bassa** | u24744931 | DevOps & Integration Engineer | TypeScript, Python, Docker, PostgreSQL, GitHub Actions | [![GitHub](https://img.shields.io/badge/-GitHub-181717?style=flat&logo=github)](https://github.com/) | [![LinkedIn](https://img.shields.io/badge/-LinkedIn-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/zaman-bassa-033673360/) |

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Technologies Used

#### Frontend
<p align="center">
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB"/>
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white"/>
  <img src="https://img.shields.io/badge/HLS.js-E30000?style=for-the-badge&logoColor=white"/>
</p>

#### Backend
<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white"/>
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socketdotio&logoColor=white"/>
</p>

#### AI / ML Pipeline
<p align="center">
  <img src="https://img.shields.io/badge/YOLOv8-00FFFF?style=for-the-badge&logoColor=black"/>
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"/>
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white"/>
  <img src="https://img.shields.io/badge/DeepSORT-000000?style=for-the-badge"/>
</p>

#### Video Ingestion
<p align="center">
  <img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white"/>
  <img src="https://img.shields.io/badge/MediaMTX-000000?style=for-the-badge"/>
</p>

#### Database & Storage
<p align="center">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Amazon_RDS-527FFF?style=for-the-badge&logo=amazonrds&logoColor=white"/>
  <img src="https://img.shields.io/badge/Amazon_S3-569A31?style=for-the-badge&logo=amazons3&logoColor=white"/>
</p>

#### DevOps & Cloud
<p align="center">
  <img src="https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white"/>
  <img src="https://img.shields.io/badge/Amazon_EC2-FF9900?style=for-the-badge&logo=amazonec2&logoColor=white"/>
  <img src="https://img.shields.io/badge/Amazon_Cognito-DD344C?style=for-the-badge&logo=amazoncognito&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>
  <img src="https://img.shields.io/badge/Amazon_CloudWatch-FF4F8B?style=for-the-badge&logo=amazoncloudwatch&logoColor=white"/>
</p>

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Branching Strategy

This project follows a **Git Flow** branching strategy:

```
main
 └── dev
      ├── feature/<name>   # new features
      └── fix/<name>       # bug fixes
```

| Branch | Purpose |
|---|---|
| `main` | Production-ready releases only |
| `dev` | Integration branch — all features merge here first |
| `feature/<name>` | Individual feature branches, branched from `dev` |
| `fix/<name>` | Bug fix branches, branched from `dev` |

All pull requests require at least **one peer review** before merging into `dev`. Direct commits to `main` are not permitted.

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>

---

## Contact Us

<div align="center">

Have questions, ideas, or want to get in touch?

[intrepid.capstone@gmail.com](mailto:intrepid.capstone@gmail.com)

<br/>

*COS 301 Capstone Project 2026 · University of Pretoria · EPI-USE Africa*

</div>

<p align="right"><a href="#-table-of-contents">↑ Back to top</a></p>
