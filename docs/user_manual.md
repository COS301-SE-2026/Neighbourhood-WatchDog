# Neighbourhood WatchDog User Manual


## 1. Getting Started

1. Open the currently approved WatchDog deployment URL.
2. Select **Create Account**.
3. Enter your **First Name**, **Last Name**, **Address**, **Email Address**, **Password**, and **Confirm Password**.
4. Submit the form.
5. Enter the confirmation code sent to your email address.
6. Once your account is confirmed, sign in using your registered credentials.


## 2. Create a Property

To register a camera, you first need a property.

1. Open **Properties** from the application navigation.
2. Select **Create Property**.
3. Enter the requested property information.
4. Save the property.

A property and a neighbourhood are separate records. Creating a property does
not automatically create or join a neighbourhood.


## 3. Create or Join a Neighbourhood

### Join an existing neighbourhood

1. Obtain a join code from the neighbourhood administrator.
2. Open **Join Neighbourhood**.
3. Enter the join code and submit the request.
4. Wait for a neighbourhood administrator to approve or reject the request.

Your request remains pending until an authorised administrator resolves it.

### Create a neighbourhood

1. Create or select the required property.
2. Open **Create Neighbourhood**.
3. Enter the neighbourhood details.
4. Save the neighbourhood and retain its generated join code securely.


## 4. Add a Camera

1. Open the relevant property.
2. Select **Add Camera**.
3. Enter the camera **Name**, **Location**, and **RTSP URL**.
4. Select a visibility setting: **Private**, **Public**, or **Neighbourhood**.
5. Save the camera.

Detection zones and confidence thresholds are configured separately from the
camera-registration form.


## 5. Configure Detection Zones and Sensitivity

1. Open the camera settings panel.
2. Draw and save a polygonal detection zone.
3. Set the camera confidence threshold.
4. Save the updated settings.

The Agent uses these settings while processing enabled cameras. A person
detection must satisfy the configured threshold before the system creates the
corresponding alert.


## 6. Set Up the WatchDog Agent

The WatchDog Agent runs on a trusted, always-on machine that can reach the
registered camera sources.

- **Windows:** run `ai/setup.bat`. It checks for Python 3.12 and starts the Agent setup application.
- **Linux:** run `ai/ai_setup.sh`. It creates the Python environment, installs dependencies, downloads model weights, and provides the commands needed to start the local services.

For the demonstrated pairing workflow, use native Windows Python 3.12. WSL cannot access the Windows credential store used by the paired Agent.


## 7. Pair the Agent and Enable Monitoring

1. Open the relevant property.
2. Generate a WatchDog Agent pairing token.
3. Enter the token in the Agent setup application before it expires.
4. Confirm that the Agent reports a paired/connected state.
5. Enable the required camera from the application.

The Agent periodically reconciles its assigned property cameras. It starts
isolated publishing and detection work only for enabled cameras, and stops
that work when a camera is disabled.


## 8. View a Live Camera

1. Select a camera you are authorised to view.
2. Wait for the playback state to change from **Connecting** to **Live**.
3. If playback cannot start, the interface should show an unavailable or offline state.
4. Close the focused camera view when finished.

The browser requests live playback only after you select a camera.


## 9. Alerts

When a qualifying person detection occurs, the system can create an alert and
broadcast it to connected dashboard clients.

1. Open **Alerts**.
2. Review the available alert information.
3. Acknowledge an alert only when a responsible person is actively handling it.
4. Follow the applicable neighbourhood or security response procedure.


## 10. Notifications

When notification delivery is enabled on the deployment, the backend can send
WhatsApp and email notifications for eligible alerts.

WhatsApp delivery requires:
- `NOTIFICATION_ENABLED=true`;
- valid Twilio configuration;
- a stored resident phone number; and
- an eligible alert.

Email delivery requires a valid user email address and working mail
configuration.


## 11. Analytics

Analytics, neighbourhood risk scoring, predictive insights, and comprehensive
response-time reporting remain part of the active product vision but should
not be presented as complete Demo 2 functionality unless verified in the
deployed application.
