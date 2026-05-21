# System Requirements Specification - Neighbourhood WatchDog

## Introduction

It is no secret that the world we live in is an unsafe place. Neighbourhood WatchDog aims to help keep our neighbourhoods safe in this unsafe world. This system uses AI to detect suspicious activity on camera systems in order to help prevent crime and respond to crime quickly.

## User Stories

### E1: Identity & Access Management

- **US-01**: As a new resident, I want to create an account using my email so that I can join my neighbourhood and start using the platform.
- **US-02**: As a registered user, I want to log in with a one-time verification code in addition to my password so that my account stays secure even if my password is compromised.
- **US-03**: As a logged-in user, I want to sign out of the platform so that my account is not accessible to anyone else using my device.
- **US-04**: As a system admin, I want to view a complete, read-only audit log of all user activity so that I can investigate any suspicious behaviour or access disputes.

### E2: Neighbourhood & Property Management

- **US-05**: As a resident, I want to create a new neighbourhood so that I can group my neighbours together and manage shared camera coverage.
- **US-06**: As a resident, I want to join an existing neighbourhood using a join code so that I can access its shared cameras and alerts.
- **US-07**: As a neighbourhood admin, I want to approve or deny requests from people wanting to join my neighbourhood so that only verified residents gain access.
- **US-08**: As a resident, I want to create a property and link it to my neighbourhood so that I can associate my home's cameras with the right community.
- **US-09**: As a neighbourhood admin, I want to assign and change roles for neighbourhood members so that each person only has access to what they need.

### E3: Camera Registration & Management

- **US-10**: As a resident, I want to register my home camera on the platform so that its footage can be monitored and analysed for security incidents.
- **US-11**: As a resident, I want to edit my camera's details or temporarily disable it so that I can keep the system up to date without fully removing the camera.
- **US-12**: As a resident, I want to permanently remove a camera I no longer own so that it stops appearing on the platform entirely.
- **US-13**: As a security officer, I want to draw detection zones on a camera view and set a confidence threshold so that I only get alerted about activity in areas that actually matter.

### E4: Video Ingestion & Live Streaming

- **US-14**: As a security officer, I want to see live video feeds from all neighbourhood cameras on my dashboard so that I can monitor multiple areas at once without switching between screens.
- **US-15**: As a security officer, I want to click on a camera feed and view it full screen so that I can inspect footage more closely when something looks suspicious.
- **US-16**: As a resident, I want to view live feeds from my own cameras on my dashboard so that I can keep an eye on my property from anywhere.

### E5: AI Detection & Behaviour Classification

- **US-17**: As a resident, I want the system to automatically detect when a person appears in a restricted zone on my camera so that I am alerted without having to watch the feed myself.
- **US-18**: As a security officer, I want the system to classify what a detected person is doing so that I can understand the severity of a situation at a glance without reviewing the footage first.
- **US-19**: As a security officer, I want the system to keep track of the same person across multiple frames using a consistent ID so that I can follow their movement without piecing together separate alerts manually.

### E6: Alert Management

- **US-20**: As a security officer, I want to see new alerts appear on my dashboard instantly without refreshing so that I can respond to incidents as they happen.
- **US-21**: As a security officer, I want to acknowledge an alert so that my team can see that someone is already handling it and avoid duplicated responses.
- **US-22**: As a security officer, I want to watch the video clip that triggered an alert so that I can judge whether the situation requires a physical response.
- **US-23**: As a security officer, I want to browse and filter past alerts so that I can review incidents that happened while I was off duty.
- **US-24**: As a resident, I want to receive a WhatsApp message and email when a high-severity alert is triggered on my camera so that I am notified even when I am not watching the dashboard.
- **US-25**: As a neighbourhood admin, I want to broadcast a critical alert to all neighbourhood members so that everyone can take precautions during a serious security incident.

### E7: Analytics & Risk Intelligence

- **US-26**: As a neighbourhood admin, I want to see charts showing how frequently alerts are occurring across the neighbourhood so that I can identify problem areas and times.
- **US-27**: As a neighbourhood admin, I want to see an overall risk score for my neighbourhood so that I can understand at a glance whether security has been getting better or worse over time.
- **US-28**: As a neighbourhood admin, I want to see how quickly alerts are being acknowledged so that I can identify response time problems and address them.
- **US-29**: As a neighbourhood admin, I want to see incident trends over time so that I can spot recurring patterns and take preventative action before problems escalate.

### E8: Autonomous Patrol Assistance

- **US-30**: As a security officer, I want the system to automatically follow a suspicious individual across cameras and show me their movement path so that I can respond without losing track of them.
- **US-31**: As a security officer, I want to receive a situational brief summarising everything the system knows about a tracked individual so that I can brief my team quickly without reviewing hours of footage.

### E9: Predictive Risk Scoring

- **US-32**: As a neighbourhood admin, I want to see predictions of which time windows and camera zones are at highest risk so that I can schedule patrols proactively rather than just reacting to incidents.
- **US-33**: As a security officer, I want to be notified when a zone's predicted risk level rises significantly so that I can increase my attention to that area before an incident actually occurs.

---

## Functional Requirements

#### R1: Video Ingestion
    R1.1: Stream Acceptance
        R1.1.1: The system shall accept live video streams from IP cameras.
        R1.1.2: The system shall accept simulated video feeds (such as pre-recorded video files). 
        R1.1.3: The system shall support multiple simultaneous incoming streams.
    R1.2: Stream Relay
        R1.2.1: The system shall relay incoming camera streams, decoupling the cameras from downstream services.
        R1.2.2: The system shall allow multiple services to consume the same camera stream simultaneously without connecting directly to the camera.
        R1.2.3 The system shall output each relayed stream in an HTTP Live Streaming (HLS) format for a browser-based preview.
    R1.3: Frame Extraction       
        R1.3.1: The system shall extract frames from incoming video streams.
        R1.3.2: Extracted frames shall be pushed to a queue for distribution to AI processing workers.
    R1.4: Format Conversion
        R1.4.1: The system shall support format conversion and re-encoding across different camera types and input sources.

#### R2: AI Detection Processing
    R2.1: Human Presence Detection
        R2.1.1: The system shall detect the presence of humans within defined camera zones. 
        R2.1.2: Video frames shall be preprocessed before analysis to improve detection accuracy.
        R2.1.3: A detection event shall be generated for each confirmed human presence, containing a confidence score, timestamp, and camera identifier. 
        R2.1.4: Detection frames shall be processed asynchronously to ensure continuous camera monitoring without interruption.
    R2.2: Scored (Emergency-Rating) Detection Events
        R2.2.1: Severity rating (LOW, MEDIUM, HIGH, or CRITICAL) will be assigned to each detection event based on its confidence score and detected behaviour type.
        R2.2.2: Alert record to be triggered only when a detection event's confidence score exceeds a configurable threshold.
        R2.2.3: All triggered alert records will be displayed on the monitoring dashboard in real time and persisted.
    R2.3: Behaviour Classification
        R2.3.1: Classify detected behaviour into predefined categories: loitering, perimeter scanning, unusual movement patterns, weapon detected, fall detected and unconscious/unresponsive detected.
        R2.3.2: The system shall use an individual's movement patterns across consecutive frames as input for behaviour classification.
        R2.3.3: The system shall support model improvement using provided CCTV datasets to improve accuracy for the target environment. 
    R2.4: Tracking (DeepSort)
        R2.4.1: Assign a persistent tracking ID to each detected individual across multiple video frames.
        R2.4.2: Maintain tracking continuity for individuals moving across multiple cameras.
        R2.4.3: The system shall use tracking data to generate a movement path summary per individual for the autonomous patrol assistance feature.
#### R3: Alert and Event Management
    R3.1: Alert triggering
        R3.1.1: Shall show the user a real-time alert on the dashboard when an event occurs (e.g. weapon detected, loitering, person detected in restricted area, etc.)
        R3.1.2: Shall show the user an alert containing information about the event, such as the time, classification, severity and location of the event, and the confidence score.
    R3.2: Alert logging (record) and history
        R3.2.1: The footage that triggered the alert should be saved and timestamped so that the user can review it later.
        R3.2.2: Shall allow user to view footage of alerts.
        R3.2.3 Access to the recordings will be scoped by the same role-based permissions as the access to the video stream.
    R3.3: Notifications
        R3.3.1: Notify the user via WhatsApp and Email when an alert is triggered providing important information about the event (e.g. time).
        R3.3.2 Other users in the neighbourhood should be alerted when there is a severe alert.
#### R4: User/Access Control
    R4.1 Scoped permissions
        R4.1.1 The system should categorise video feeds by 3 different visibilities: public, restricted and private. Restricted video feeds are those which residents have selected to make viewable by security officers.
        R4.1.2 Security officers and neighbourhood admins may view all public, and restricted video streams
        R4.1.3 Residents may view their own private and restricted video streams of cameras on their own property and all public streams. 
        R4.1.4 System admin may see all public video streams.
    R4.2 Select visibility of video feeds
        R4.2.1 Shall allow residents to choose which cameras’ streams will be public, restricted or private.
        R4.2.2 Shall allow neighbourhood admins to add camera streams that will be public
    R4.3 Multi-Factor Authentication
        R4.3.1 Will require all users to log in using Multi-Factor Authentication methods.
    R4.4 Audit Trail
        R4.4.1 Log all user activity for  audit purposes.

#### R5: Dashboard
    R5.1: Live Alert Feed
        R5.1.1: The dashboard shall display incoming alerts in real-time without requiring a page refresh.
        R5.1.2: Each alert displayed shall include the camera name, detection type, severity, confidence score, and timestamp.
        R5.1.3: The dashboard shall allow a user to acknowledge an alert, updating its status accordingly.
        R5.1.4: The dashboard shall visually distinguish between unacknowledged, acknowledged, and resolved alerts.
    R5.2: Camera Status Display
        R5.2.1: The dashboard shall display the online and/or offline status of each registered camera.
        R5.2.2: The dashboard shall update camera status indicators in real-time.
    R5.3: Live Stream Preview
        R5.3.1: The dashboard shall display a live stream preview for each camera.
        R5.3.2: The dashboard shall allow a user to select and enlarge a specific camera feed for closer inspection.
    R5.4: Incident History
        R5.4.1: The dashboard shall provide a view of all past alerts, filterable by camera, detection type, date, and status.
        R5.4.2: The dashboard shall allow a user to view the footage clip associated with a historical event.
    R5.5: Administrative Configuration
        R5.5.1: The dashboard shall allow an administrator to register and remove cameras.
        R5.5.2: The dashboard shall allow a user to define and configure restricted zones per camera upon camera registration.
        R5.5.3: The dashboard shall allow a security officer or neighbourhood administrator to set the confidence threshold for alert triggering.
    R5.6: Responsiveness
        R5.6.1: The dashboard shall be accessible and functional on both desktop and mobile browsers.

#### R6 Analytics and Reporting
    R6.1 Risk Scoring
        R6.1.1 The system shall calculate a risk score for each neighbourhood based on historical incident data and alert frequency.
        R6.1.2 The system shall integrate incident severity levels and time into the risk score calculations.
        R6.1.3 Update the risk score of zones and neighbourhoods weekly.
        R6.1.4 The system shall classify risk scores into High, Medium and Low risk
        R6.1.5 The system shall maintain historical risk score records for analysis of trends.
    R6.2 Alert Frequency Dashboard
        R6.2.1 Combine alert data over configurable time intervals
        R6.2.2 The system shall allow a user to group alerts by time period, camera or zone, property and severity
        R6.2.3 Display alert frequency by selected filters using graph visualizations
        R6.2.4 Update dashboard when new alerts are recorded.
    R6.3 Response Time Metrics 
        R6.3.1 Record timestamp when an alert is generated and when the security officer marks the alert as acknowledged indicating that it has been dealt with.
        R6.3.2 Generate metrics on the average response times in a neighbourhood
    R6.4 Incident Trend Analysis
        R6.4.1 Generate and show aggregate incident data over time
        R6.4.2 Group incidents based on time period, location and incident type.
        R6.4.3 Identify increases in incident frequency over time
        R6.4.4 Identify recurring incident patterns
        R6.4.5 Use graphical representation for incident trends
        R6.4.6 Allow user to filter incident trends based on date ranges and incident types

#### R7 User Registration
    R7.1 User Registration
        R7.1.1 Allow new resident to register an account
        R7.1.2 Shall verify the resident’s email address by sending an OTP to the user’s email address.
    R7.2 Neighbourhood Creation
        R7.2.1 Allow a resident to create a new neighbourhood 
        R7.2.2 System create a unique join code for distribution
    R7.3 Neighbourhood Association
        R7.3.1 User can select or provide neighbourhood identifier to register for neighborhood
        R7.3.2 User can enter a code to enter a specific neighbourhood
        R7.3.3 User can request to join a neighbourhood
        R7.3.4 Admin User able to accept or deny requests to join neighbourhoods
    R7.4 Camera Registration
        R7.4.1 Allow user to register a new camera
            R7.4.1.1 User must select a privacy type for the camera
            R7.4.1.2 User may select a name and location for camera
        R7.4.2 Allow user edit properties of camera
            R7.4.2.1 User able to change name and location
            R7.4.2.2 Disable camera permanently or temporarily
            R7.4.2.3 Allowed to deregister the camera
        R7.4.3 System will associate the camera to a property
    R7.5 User Authentication
        R7.5.1 User signing in with extra verification of OTP activating a new session
        R7.5.2 Allow user to sign out terminating active session

#### R8 Property Management
    R8.1 Property Creation
        R8.1.1 A resident may create a new property and they will become the property admin for that property.
        R8.1.2 A user can request to add a property to a neighbourhoods.
        R8.1.3 The neighbourhood admin may approve or reject the request to a neighbourhood.
    R8.2 Property Membership Management
        R8.2.1 Property admin may invite residents to a property (people that live there as well). 
        R8.2.2 Property admin may remove residents from a property.
        R8.2.3 Residents can leave property voluntarily.
        R8.2.4 Residents shall receive a notification when invited to a property and be able to accept or decline the invitation.
    R8.3 Property Ownership and Control
        R8.3.1 Property admin may transfer property admin ownership to another user (when moving out).
        R8.3.2 A resident who is part of a property is allowed to request ownership of a property.
    R8.4 Property-Camera Association
        R8.4.1 Associate Cameras with the property
        R8.4.2 Admin can manage cameras within property

#### R9 Security Management
    R9.1 Company Registration
        R9.1.1 Security System allows the company to register an account 
        R9.1.2 Email verification before activating the company account
    R9.2 Security Personnel Management
        R9.2.1 Company is able to register multiple security personnel accounts 
        R9.2.2 Company has overview of security personnel
        R9.2.3 Company can allocate personnel to neighbourhoods they joined.
        R9.2.4 Company able to deallocate personnel from neighbourhoods
        R9.2.5 Company can see all incidents the personnel have responded to.
    R9.3 Neighbourhood association
        R9.3.1 Companies can view all public camera feeds within neighbourhood
        R9.3.2 System allows companies to view all restricted cameras
        R9.3.3 Can view active alerts of neighbourhoods
        R9.3.4 Can view all neighbourhoods they have joined and the personnel allocated to the neighbourhoods
        R9.3.5 View incident history of neighbourhoods 
        R9.3.6 View all invites to neighbourhoods
	    R9.3.6.1 Company can choose to view the neighbourhood and its details
	    R9.3.6.2 Company is able to accept or decline requests to join the neighbourhoods

    R9.4 Security Response Management
        R9.4.1 View all alerts that have been dispatched
        R9.4.2 Change the status of the alerts list the alsert statuss here
        R9.4.3 View respondees of the alert
        R9.4.4 View the timeline of the alert and the state changes


## API Service Contracts

### 1. Camera Registration Service

**Description:** Allows a user (Neighbourhood Administrator / Resident) to register a camera on their property, validate the stream, and make it available for live preview on the dashboard.

**Inputs:**
- `streamUrl` (string) – Real-Time-Stream-Protocol (RTSP) URL of the stream
- `ipAddress` (string) – IP address of the camera device
- `cameraName` (string) – A human-readable label for the camera
- `location` (string) – Physical location description (e.g. "Backyard")
- `privacyType` (enum: PUBLIC | RESTRICTED | PRIVATE) – Visibility setting for the stream

**Outputs:**
- `cameraId` (UUID) – Unique identifier assigned to the registered camera
- `status` (enum: ONLINE | OFFLINE | ERROR) – Initial connection status after registration
- `hlsStreamUrl` (string) – HTTP Live Stream (HLS) URL for browser-based live preview

**Usage / Interaction Rules:**
- Client will send a POST request to `/cameras/register` with the inputs in JSON format.
- The user must be authenticated with a Neighbourhood Admin or Resident role; else a 401 status code is returned.
- On submission, the system attempts to connect to the RTSP stream; if the connection fails, the camera is marked as OFFLINE.
- If the streamUrl is already registered in the neighbourhood, a 409 status code is returned.
- On success, a 201 status code is returned with the cameraId and its hlsStreamUrl.

---

### 2. Video Ingestion and Human Detection Service

**Description:** Ingests an active camera stream, extracts frames, and runs YOLOv8 detection to determine whether a human is present within the camera’s defined zone.

**Inputs:**
- `cameraId` (UUID) – Identifier of the camera stream to process
- `frameInterval` (integer) – Interval in seconds between frame extractions
- `confidenceThreshold` (float, 0-1) – The minimum confidence score for a detection to be recorded
- `zoneBoundary` (JSON) – Coordinates of the restricted zone to apply as mask, protecting "privatized" areas

**Outputs:**
- `detectionEventId` (UUID) – Unique identifier for the detection event
- `cameraId` (UUID) – Camera that produced the detection
- `timeStamp` (datetime) – Time the frame was captured
- `humanDetected` (boolean) – Whether a human was found within the zone
- `confidenceScore` (float) – Model confidence score for the detection
- `thumbnailUrl` (string) – URL of the annotated frame thumbnail

**Usage / Interaction Rules:**
- This service is triggered internally by the Celery Worker pipeline. It is not directly called by the client.
- Frames are extracted from the MediaMTX relay using FFmpeg and published to a Kafka topic for processing by the Celery Workers.
- OpenCV applies the zoneBoundary mask before passing the frame to YOLOv8; detections outside the zone are discarded.
- On a valid detection, the event is saved to the database, and the annotated thumbnail is uploaded to the cloud object storage.
- If the camera stream is unavailable, the worker logs the failure and skips the frame without crashing.

---

### 3. Alert Display Service

**Description:** Delivers real-time alerts to the monitoring dashboard and exposes camera status indicators, ensuring Security Officers have immediate situational awareness.

**Inputs:**
- `detectionEventId` (UUID) – The detection event that triggered the alert
- `userId` (UUID) – The authenticated user requesting the dashboard feed
- `filters` (object, optional) – Optional filters: `{ cameraId, severityLevel, status }`

**Outputs:**
- `alertId` (UUID) – Unique identifier for the alert
- `cameraName` (string) – Name of the camera that triggered the alert
- `detectionType` (enum: HUMAN_PRESENCE | LOITERING | WEAPON_DETECTED | PERIMETER_SCAN) – Classification of the detection
- `severityLevel` (enum: LOW | MEDIUM | HIGH | CRITICAL) – Severity rating of the alert
- `confidenceScore` (float) – Confidence score of the underlying detection
- `timestamp` (datetime) – Time the alert was generated
- `status` (enum: OPEN | ACKNOWLEDGED | RESOLVED) – Current alert status

**Usage / Interaction Rules:**
- Alerts are pushed to the dashboard in real-time via WebSocket; the client subscribes on dashboard load.
- The client connects to `ws://<host>/ws/alerts` with a valid auth token; unauthenticated connections are rejected with a 401.
- Role-based filtering is applied server-side: a Resident only receives alerts for cameras in their neighbourhood; a Security Officer receives all alerts within their neighbourhood.
- Camera status indicators are polled from MediaMTX every 10 seconds and broadcast to all connected dashboard clients.
- A Security Officer can acknowledge an alert by sending a PATCH request to `/alerts/{alertId}/status` with `{ "status": "ACKNOWLEDGED" }`; the update is broadcast to all connected clients immediately.

---

### 4. User Registration Service

**Description:** Allows a new user to create an account, verify their identity, and gain access to the system.

**Inputs:**
- `name` (string) – Full name of the user
- `email` (string) – Email address used as the unique identifier
- `password` (string) – User’s chosen password
- `role` (enum: NEIGHBOURHOOD_ADMIN | SECURITY_OFFICER | RESIDENT) – Requested role

**Outputs:**
- `userId` (UUID) – Unique identifier assigned to the new user
- `email` (string) – Confirmed email address of the registered user
- `otpSent` (boolean) – Confirms whether the OTP verification email was dispatched

**Usage / Interaction Rules:**
- Client sends a POST request to `/auth/register` with inputs in JSON format.
- If the email is already registered, a 409 is returned.
- On submission, an OTP is sent to the provided email; the account is inactive until OTP is verified.
- Client sends a POST request to `/auth/verify-otp` with `{ "email": "...", "otp": "..." }` to activate the account.
- If the OTP is incorrect or expired, a 401 is returned.
- On successful verification, a 201 is returned and the user can log in.
- Passwords must meet minimum complexity requirements; a 422 is returned if validation fails.

---

### 5. User Login Service

**Description:** Authenticates a user via email and password, enforces MFA for user roles, and returns an access token for subsequent authenticated requests.

**Inputs:**
- `email` (string) – Registered email address of the user
- `password` (string) – User’s password
- `mfaCode` (string, optional) – Time-based One-Time Password (TOTP) code required for user roles

**Outputs:**
- `accessToken` (string) – JWT token used for authenticated requests
- `refreshToken` (string) – Token used to obtain a new access token on expiry
- `expiresAt` (datetime) – Time at which the access token becomes invalid
- `role` (enum: SYSTEM_ADMIN | NEIGHBOURHOOD_ADMIN | SECURITY_OFFICER | RESIDENT) – Role of the authenticated user

**Usage / Interaction Rules:**
- Client sends a POST request to `/auth/login` with inputs in JSON format.
- If credentials are invalid, a 401 is returned; the failed attempt is written to the audit log.
- If the user’s role is SYSTEM_ADMIN, NEIGHBOURHOOD_ADMIN, RESIDENT, or SECURITY_OFFICER, MFA is required; a 403 is returned if mfaCode is absent or incorrect.
- On success, a 200 is returned with accessToken and refreshToken.
- The login event is written to the audit log with `mfa_used` and `success` in metadata.
- Access token expiry is 15 minutes; clients must use refreshToken to obtain a new one via POST `/auth/refresh`.

---

### 6. Alert Acknowledgement Service

**Description:** Allows a Security Officer to acknowledge an open alert, updating its status and reflecting the change across all connected dashboard clients in real-time.

**Inputs:**
- `alertId` (UUID) – Unique identifier of the alert being acknowledged
- `userId` (UUID) – Identifier of the Security Officer performing the acknowledgement

**Outputs:**
- `alertId` (UUID) – Identifier of the updated alert
- `status` (enum: ACKNOWLEDGED) – Updated alert status
- `acknowledgedBy` (UUID) – User ID of the Security Officer who acknowledged the alert
- `acknowledgedAt` (datetime) – Timestamp of the acknowledgement

**Usage / Interaction Rules:**
- Client sends a PATCH request to `/alerts/{alertId}/status` with `{ "status": "ACKNOWLEDGED" }` in JSON format.
- Caller must be authenticated with a Security Officer role or higher; a 403 is returned otherwise.
- If the alert does not exist, a 404 is returned.
- If the alert is already ACKNOWLEDGED or RESOLVED, a 409 is returned.
- On success, a 200 is returned and the status change is broadcast to all connected dashboard clients via WebSocket.
- The acknowledgement is written to the audit log with `previous_status` and `new_status` in metadata.

---

### 7. Historical Alert Footage Service

**Description:** Allows a Security Officer to retrieve and view the footage clip associated with a past alert from the incident history view.

**Inputs:**
- `alertId` (UUID) – Unique identifier of the alert whose footage is being requested
- `userId` (UUID) – Identifier of the user requesting the footage

**Outputs:**
- `alertId` (UUID) – Identifier of the alert
- `footageUrl` (string) – Pre-signed S3 URL to the footage clip
- `timestamp` (datetime) – Time the footage was recorded
- `expiresAt` (datetime) – Time at which the pre-signed URL expires
- `detectionType` (enum: HUMAN_PRESENCE | LOITERING | WEAPON_DETECTED | PERIMETER_SCAN) – Classification of the detection that triggered the alert

**Usage / Interaction Rules:**
- Client sends a GET request to `/alerts/{alertId}/footage`.
- Caller must be authenticated with a Security Officer role or higher; a 403 is returned otherwise.
- If the alert does not exist, a 404 is returned.
- If the footage clip has not yet been uploaded (e.g. upload still in progress), a 202 is returned with `{ "message": "footage not yet available" }`.
- If the footage has been archived to cold storage, a 202 is returned with `{ "message": "footage being retrieved from archive" }`.
- On success, a 200 is returned with a pre-signed S3 URL valid for 15 minutes.
- Access is scoped to the user’s neighbourhood; requesting footage from another neighbourhood’s alert returns a 403.
- The view event is written to the audit log with `alertId` as `targetId` and `target_type` as `Alert`.

---

## Use Cases

![Use Cases P1 - UCD1](images/Use%20Cases%20P1%20-%20UCD1.png)

R1: Video Ingestion
UC1.1 - Register a Camera Stream (Abstract) 
High-Level:
TUCBW: A Neighbourhood Administrator / Resident can add a new camera to a property..
TUCEW: The Administrator or Resident sees the camera stream registered and appearing on the dashboard with a live preview.
UC1.2 - View Live Camera Feed (Abstract) 
High-Level:
TUCBW: A user selects a camera from the dashboard.
TUCEW: The user sees a live stream preview of the selected camera feed in their browser.

![Use Cases P1 - UCD2](images/Use%20Cases%20P1%20-%20UCD2.png)

R2: User and Access Control
UC2.1 - Log In with Multi-Factor Authentication (Abstract)
High-Level:
TUCBW: A user enters their credentials on the login screen.
TUCEW: The user has successfully completed MFA verification and sees the dashboard.
UC2.2 - Set Camera Visibility (Abstract)
High-Level:
TUCBW: A Resident navigates to their camera settings and selects a visibility option for one of their cameras.
TUCEW: The Resident sees the camera's visibility updated to public, restricted, or private.
UC2.3 - View Permitted Camera Streams (Abstract)
High-Level:
TUCBW: A Security Officer / Neighbourhood Administrator opens the live streams view on the dashboard.
TUCEW: The Security Officer / Neighbourhood Administrator sees all public and restricted camera streams they are permitted to view, with no access to private streams.

![Use Case P2 - UCD3](images/Use%20Case%20P2%20-%20UCD3.png)

R3: Dashboard
UC3.1 - Monitor Live Alert Feed (Abstract)
High-Level:
TUCBW: A User opens the dashboard.
TUCEW: The Security Officer sees all incoming alerts updating in real time, each showing camera name, detection type, severity, confidence score, and timestamp.
UC3.2 - Filter Incident History (Abstract)
High-Level:
TUCBW: A Security Officer navigates to the incident history view and applies filters.
TUCEW: The Security Officer sees a filtered list of past alerts matching the selected camera, detection type, date range, or status.
UC3.3 - Configure Alert Threshold (Abstract)
High-Level:
TUCBW: A Security Officer or Neighbourhood Administrator navigates to the configuration panel and adjusts the confidence threshold slider for a camera.
TUCEW: The Security Officer or Neighbourhood Administrator sees a confirmation that the new threshold value has been saved and is now active.
UC3.4 - Track an Individual Across Cameras (Abstract)
High-Level:
TUCBW: A Security Officer selects a detected individual from the alert feed to view their movement path. 
TUCEW: The Security Officer sees the individual's tracking ID and full movement path summary across all cameras. 
UC3.5 - Acknowledge an Alert (Abstract)
High-Level:
TUCBW: A Security Officer views an unacknowledged alert on the dashboard.
TUCEW: The Security Officer sees the alert status updated to acknowledged on the dashboard.
UC3.6 - Review Historical Alert Footage (Abstract)
High-Level:
TUCBW: A Security Officer / Resident selects a past alert from the incident history view.
TUCEW: The Security Officer /Resident is able to view the footage clip associated with that alert event.
UC3.7 - Receive Alert Notification (Abstract)
High-Level:
TUCBW: A Security Officer / Resident has registered for notifications and a high-severity alert is triggered. 
TUCEW: The Security Officer / Resident has received a notification via WhatsApp or email containing the event details. 

![Use Case P2 - UCD4](images/Use%20Case%20P2%20-%20UCD4.png)

R4: Analytics and Reporting
UC4.1 - View Neighbourhood Risk Score (Abstract)
High-Level:
TUCBW: A user opens the analytics page.
TUCEW: The user sees the current risk score for their neighbourhood, categorised as LOW, MEDIUM, or HIGH, calculated from historical incident data.
UC4.2 - Analyse Incident Trends (Abstract)
High-Level:
TUCBW: A user applies date range and incident type filters in the trend analysis view.
TUCEW: The user sees graphical representations of incident trends over the selected period, grouped by time, location, and type.

![Use Case P2 - UCD5](images/Use%20Case%20P2%20-%20UCD5.png)

R5: User Registration
UC5.1 - Register a New Account (Abstract)
High-Level:
TUCBW: A new user navigates to the registration page and submits their details.
TUCEW: The user sees a confirmation that their account has been created and can now log in.
UC5.2 - Register as Security Officer(Abstract)
High-Level:
TUCBW: The Security Officer once registered as a user can choose to join the waiting pool until they are assigned to a Neighbourhood.
TUCEW: The Security Officer gets a confirmation stating that they have been added to the waiting pool.

![Use Case P3 - UCD6](images/Use%20Case%20P3%20-%20UCD6.png)

R6: Property Management
UC6.1 - Create a Property (Abstract)
High-Level:
TUCBW: A Resident creates a new property.
TUCEW: The property is created and the Resident is presented with the option to add cameras to the property and to add the property to a neighbourhood.

UC6.2 - Invite Resident to Property (Abstract)
High-Level:
TUCBW: A Property Administrator searches for a user and sends them an invitation to join the property.
TUCEW: The Property Administrator sees a confirmation that the invitation has been sent and the recipient receives a notification inviting them to join the property.
UC6.3 - Respond to Property Invitation
High-Level:
TUCBW: A Resident receives a notification that they have been invited to join a property and either accepts or rejects it.
TUCEW: The Resident sees confirmation that they have accepted or declined the invitation.
UC6.4 - Remove resident from property
High-Level:
TUCBW: A Property Administrator can remove a resident from a property.
TUCEW: The Resident will be notified that they have been removed from a property and the property Administrator receives a notification that the resident has been removed. 


![Use Case P3 - UCD7](images/Use%20Case%20P3%20-%20UCD7.png)

R7 Neighbourhood Management

UC7.1 - Create a Neighbourhood (Abstract)
High-Level:
TUCBW: A Resident with a property creates a new neighbourhood.
TUCEW: The user sees the newly created neighbourhood and receives a unique join code for distribution to residents.
UC7.2 - Remove property from Neighbourhood (Abstract)
High-Level
TUCBW: A Neighbourhood Administrator can remove the property from the neighbourhood.
TUCEW: The Neighbourhood Administrator views a confirmation dialogue to confirm that the property has been removed and the Residents of the property receive notification stating that their property has been removed from the neighbourhood.

UC7.3 - Request to Add Property to Neighbourhood (Abstract)
High-Level
TUCBW: A Property Administrator requests to add a property to a neighbourhood using the neighbourhood’s join code.
TUCEW: The Neighbourhood Administrator receives the request to add the property to the neighbourhood and can accept or reject it.
UC7.4 - Request to Add Property to Neighbourhood Approved (Abstract)
High-Level
TUCBW: A Neighbourhood Administrator approves the request to add a property to the neighbourhood.
TUCEW: The property is added and all its public and restricted cameras are visible to the other Users linked to that neighbourhood as well as the Security Officer.
UC7.5 - Request to Add Property to Neighbourhood Rejected (Abstract)
High-Level
TUCBW: A Neighbourhood Administrator rejects the request to add a property to the neighbourhood.
TUCEW: The Property Administrator is presented with a notification informing them that the request has been rejected and they are unable to submit another request for 24 hours.

UC7.6 - Adding a Security Officer to a Neighbourhood (Abstract)
High-Level:
TUCBW: The Neighbourhood Administrator can select a Security Officer to invite to the neighbourhood from a list of existing officers.
TUCEW: The Security Officer can accept or reject the invitation to join the neighbourhood.


---

## Domain Model

![Architectural Diagram](images/NWD.drawio.svg)

## Architectural Requirements
 
### Quality Requirements
 
The quality requirements are derived directly from the non-functional requirements and drive the architectural decisions made in this system.
 
#### Performance
 
- The system shall ingest and process video streams with a latency of less than 4 ms from capture to dashboard display.
- The system shall support up to 100 concurrent video streams without frame loss.
- AI detection processing shall complete within 1 second per frame.
- Alerts shall appear on the dashboard within 2 seconds of detection.
- Notifications shall be delivered within 5 seconds of alert generation.
#### Scalability
 
- The system shall scale to support 1000+ cameras per neighbourhood.
- AI workers and streaming services shall support horizontal scaling independently of one another.
- The frame queue shall support a burst load of at least 10,000 frames per minute.
#### Security
 
- All video streams and API communication shall use TLS 1.2+ encryption.
- Multi-Factor Authentication shall be enforced for all users.
- Role-Based Access Control shall restrict access to video streams and recordings based on user role.
- User sessions shall expire after 15 minutes of inactivity.
- All user actions shall be logged to an append-only audit trail.
#### Accuracy
 
- Human detection accuracy shall be at least 60%.
- Behaviour classification accuracy shall be at least 80%.
#### Reliability
 
- The system shall maintain 99% uptime.
- Video ingestion failures on one stream shall not affect other active streams.
- The system shall recover from service failure within 2 minutes.
- The detection pipeline shall guarantee no loss of critical alert events.
#### Usability
 
- Users shall be able to interpret and respond to alerts within 5 seconds of viewing.
- The dashboard shall update in real time without manual refresh.
- The system shall be fully usable on desktop and mobile browsers.
#### Maintainability
 
- The system shall use a modular architecture with clearly separated subsystems.
- AI models shall be updatable without system downtime.
- Code shall maintain greater than 70% test coverage.
#### Compatibility
 
- The system shall support IP cameras from different manufacturers with different video formats.
- Video output shall comply with HLS standards for browser playback.
- The dashboard shall support the latest versions of major browsers including Chrome and Firefox.
#### Auditability
 
- All detection events, alerts, and user actions shall be logged.
- Audit logs shall be retained for at least 90 days.
- Audit logs shall support filtering by user, time, and action type.
#### Data Retention and Storage
 
- Alert-triggered video clips shall be stored for up to 90 days.
- Storage systems shall support retrieval of video footage within 3 seconds.
#### Compliance
 
- The system shall comply with the Protection of Personal Information Act (POPIA).
- Personal data shall be collected for specific, lawful purposes and shall not be retained longer than necessary.
- Users shall be informed that video surveillance is in operation.
- The system shall support data subject access requests.
- All personal data shall be stored securely and protected against unauthorised access or breaches.
---
 
### Architectural Patterns
 
![Architectural Diagram](images/Architecture%20Diagram.drawio.svg)

#### Microservices Architecture
 
Neighbourhood WatchDog is structured as a set of independently deployable microservices, each responsible for a single bounded context. The six primary subsystems — Video Ingestion, AI Detection, Alert Management, User and Access Control, the Monitoring Dashboard, and Data Storage — are deployed as separate containerised services. This allows each subsystem to be scaled, updated, and maintained independently without affecting the others. For example, AI detection workers can be scaled horizontally during high-traffic periods without redeploying the dashboard or authentication services.
 
#### Event-Driven Architecture
 
The AI detection pipeline is built around an event-driven model. When FFmpeg extracts a frame from a camera stream, it publishes the frame to a Kafka topic. Celery workers consume from this topic asynchronously, process the frame through YOLOv8 and DeepSORT, and publish a detection event if a person is confirmed. The alert service then consumes detection events and publishes alerts to the dashboard via WebSocket. This decoupling ensures that no single service blocks another, and that bursts in camera activity are absorbed by the Kafka queue rather than propagating as latency spikes downstream.
 
#### Layered Architecture (within the Dashboard)
 
The monitoring dashboard follows a layered architecture internally: a presentation layer (React components), a state management layer (handling WebSocket subscriptions and alert state), and a data access layer (API calls to the FastAPI backend). This separation keeps UI concerns isolated from data fetching logic and makes the dashboard easier to test and maintain.
 
#### Repository Pattern (Data Access)
 
All database access is abstracted behind repository classes in the FastAPI backend. No route handler interacts with PostgreSQL directly — it calls a repository method which encapsulates the query logic. This makes it straightforward to swap or mock the database layer during testing and keeps business logic out of SQL queries.
 
---
 
### Design Patterns
 
#### Observer Pattern
 
The real-time alert delivery system is built on the Observer pattern. The dashboard WebSocket connection acts as a subscriber. When a detection event produces an alert, the alert service notifies all subscribed dashboard clients immediately. This allows multiple Security Officers to receive the same alert simultaneously without polling.
 
#### Strategy Pattern
 
Behaviour classification in the AI pipeline uses the Strategy pattern. Each behaviour type — loitering, perimeter scanning, weapon detection, fall detection — is implemented as a separate classification strategy. The classifier selects the appropriate strategy at runtime based on the detection event type. This makes it straightforward to add new behaviour types without modifying existing classification logic.
 
#### Factory Pattern
 
The video stream handler uses a Factory pattern to instantiate the correct stream reader based on the input source type. A local video file, an RTSP stream, and a simulated feed are all handled by different implementations of a common interface. The factory selects the correct implementation at runtime based on the camera configuration, keeping the rest of the pipeline unaware of the source type.
 
#### Middleware Pattern
 
The FastAPI backend uses a middleware chain for cross-cutting concerns. Authentication verification, audit logging, and request timing are all implemented as middleware layers that wrap every incoming request. This keeps route handlers focused on business logic and ensures concerns like audit logging are applied consistently without being duplicated across every endpoint.
 
---
 
### Constraints
 
#### Budget
 
The project operates within a budget of R5,000 provided by EPI-USE Africa. All infrastructure choices are constrained to AWS Free Tier instances and student credits. GPU-accelerated inference instances are not available within this budget; the AI pipeline must perform acceptably on standard CPU instances (t3.medium or equivalent). GPU acceleration may be introduced in later sprints if student credits allow.
 
#### Timeline
 
The project runs from April 2026 to October 2026 across four demo milestones. Architectural decisions must favour simplicity and deliverability within two-week sprints over theoretical optimality. Features that cannot be delivered within the sprint cadence are deferred to later milestones.
 
#### Hardware
 
The system is constrained to a Tapo IP camera for live stream testing during development. The camera outputs H.264 video at 640×360 via RTSP stream2. The system must function correctly on this hardware during Demo 1. Support for additional camera manufacturers and resolutions is a later sprint concern.
 
#### Datasets
 
The AI pipeline is constrained to the following datasets provided by the client for model training and evaluation: the CCTV Action Recognition Dataset, Real Time Anomaly Detection in CCTV Surveillance, CCTV Weapon Dataset, CCTV Knife Detection Dataset, and CCTV Incident Dataset for Fall and Lying Down Detection. No external datasets may be used without client approval.
 
#### Regulatory
 
The system must comply with the Protection of Personal Information Act (POPIA). This constrains how video footage and personal data are stored, retained, and accessed. Footage may not be retained longer than 90 days. Users must be informed that surveillance is in operation. Data subject access requests must be supported. These constraints directly inform the retention policy configuration, audit logging requirements, and neighbourhood-level data isolation enforced through PostgreSQL row-level security.
 
#### Platform
 
The system must be delivered as a responsive web application accessible via desktop and mobile browsers. A native mobile application is out of scope for the current project. The dashboard must function on the latest versions of Chrome and Firefox as a minimum.
 
#### Team
 
The system is developed by a team of five third-year Computer Science students. Architectural decisions must account for the team's existing skill set. Technologies requiring significant upskilling — such as real-time video processing and Kafka stream management — are introduced incrementally across sprints rather than all at once, and foundational upskilling is prioritised before Sprint 1 development begins.
 
---
 
## Technology Requirements
 
### Frontend
 
**Next.js and TailwindCSS:** Next.js provides server-side rendering for fast initial page loads and reloads, which is important for a security dashboard where operators need to see things almost immediately. TailwindCSS removes the need to write and maintain custom CSS files.
 
**WebSocket:** Allows for two-way communication between the server and the browser when the server pushes alerts to the browser without needing to refresh, and for when the operator acknowledges or responds to the alert.
 
**HLS.js:** Handles live-stream preview and playback of recorded footage in the dashboard. Plays RTSP-sourced streams in the browser over standard HTTP. No plugins or additional infrastructure are required. MediaMTX outputs HLS natively; no extra conversion step is needed.
 
### Backend
 
**FastAPI:** The entire AI pipeline runs in Python, so using FastAPI keeps the backend in the same language, eliminating the need for a separate microservice overhead. Moreover, FastAPI handles many simultaneous camera frame events concurrently without threads blocking each other.
 
**Redis:** When multiple cameras detect events simultaneously, the backend needs a buffer to absorb the spike without dropping events or overwhelming the AI workers. Redis acts as that buffer. Detection events are pushed to a Redis queue and processed by Celery workers at a controlled rate. Also used for session caching to reduce database load on repeated auth checks.
 
**Celery:** AI processing jobs should not block the API. Celery runs background tasks asynchronously. Frame analysis, alert generation, footage retention cleanup, and scheduled reports all run as Celery tasks. Uses Redis as the message broker, so no additional queue infrastructure is needed.
 
### Auth
 
**AWS Cognito:** The system needs role-based access control. AWS Cognito is the natural choice since the project is fully hosted on AWS and it integrates natively with EC2, RDS, and S3 without additional configuration. Free tier supports up to 50,000 monthly active users. RBAC is handled via Cognito User Pools and Groups, and MFA is supported out of the box. Keeping auth within AWS also means one less external account and billing relationship to manage.
 
### AI/ML Pipeline
 
**YOLOv8 (Ultralytics):** The system must detect human presence within defined zones and identify potential intrusions. YOLOv8 is the current industry standard for real-time object detection, offering the best balance of speed and accuracy. It runs fast enough for near-real-time frame analysis on both GPU and modern CPU, and supports fine-tuning on custom datasets — necessary given the constrained CCTV datasets provided.
 
**DeepSORT:** Autonomous patrol assistance mode requires tracking an individual across multiple cameras and generating a movement path summary. DeepSORT is a multi-object tracking algorithm that pairs directly with YOLO detections, assigning persistent IDs to detected persons across frames and camera feeds.
 
**PyTorch + OpenCV:** Work as a unit in the detection pipeline. OpenCV handles all image processing, PyTorch runs the AI. OpenCV extracts frames from the video stream, resizes and preprocesses them for model input, applies zone masks to define restricted areas, and annotates output frames with bounding boxes. PyTorch powers the actual inference and handles fine-tuning of detection models on the provided CCTV datasets. YOLOv8 and DeepSORT both run on PyTorch under the hood.
 
### Video Ingestion
 
**FFmpeg:** The system must ingest both live RTSP streams from cameras and recorded video files. FFmpeg handles format conversion, frame extraction, and re-encoding across a wide range of camera types and input sources. Both live RTSP streams and recorded video files are supported.
 
**MediaMTX:** Acts as an RTSP relay server sitting between cameras and the backend. Rather than each backend service connecting directly to cameras — which creates tight coupling and limits how many consumers can access a stream — MediaMTX receives camera streams once and distributes them to multiple subscribers. Outputs HLS natively, feeding directly into HLS.js for dashboard stream preview.
 
### Database
 
**PostgreSQL (AWS RDS):** Handles all structured data, such as user accounts, roles, alert logs, audit trails, camera configurations, and incident records. PostgreSQL is mature, open-source, and has row-level security built in, which directly supports the neighbourhood isolation requirement (no cross-neighbourhood data access). Runs as a managed instance on AWS RDS.
 
### Object Storage
 
**AWS S3:** Video clips and snapshots generated by the AI pipeline need object storage because relational databases are not suited for binary media files. S3 is fully cloud-hosted with no infrastructure to manage, and integrates natively with the rest of the AWS stack. S3 also supports tiered storage (S3 Standard for recent footage, S3 Glacier for archival) with configurable retention policies per camera.
 
### DevOps
 
**Docker and Docker Compose:** All services are containerised with Docker for consistent and reproducible deployments. Docker Compose defines and runs the full multi-container stack with a single command. It deploys directly to EC2 instances without additional orchestration tooling.
 
**AWS EC2:** Provides the virtual machines that host all containerised services. Two EC2 instances cover the full stack: one for the application services (FastAPI, Redis, Celery) and one for AI inference and MediaMTX. Both run on standard CPU instances (t3.medium or equivalent) covered under the AWS Free Tier or student credits. GitHub Actions handles automated deployment to EC2 on each push to main.
 
### Monitoring
 
**AWS CloudWatch:** Built into AWS at no extra cost, covering uptime alerts, basic health checks, log aggregation, and resource usage dashboards.
 
### Cloud
 
**AWS:** Single cloud provider for all infrastructure to avoid cross-cloud egress costs. EC2, RDS, and S3 map directly to the project's infrastructure needs. Standard EC2 CPU instances (t3.medium) are sufficient for prototype scale and are covered under the AWS Free Tier and student credits, keeping compute costs within the R5,000 budget.
