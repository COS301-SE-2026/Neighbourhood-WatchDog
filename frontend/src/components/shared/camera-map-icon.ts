import { divIcon } from "leaflet";

export const CAMERA_MAP_ICON = divIcon({
  className: "watchdog-camera-icon",
  iconSize: [22, 26],
  iconAnchor: [11, 26],
  popupAnchor: [0, -26],
  html: `
    <svg
      class="watchdog-camera-icon__svg"
      width="22"
      height="26"
      viewBox="0 0 34 38"
      role="img"
      aria-label="Camera position"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>Camera position</title>

      <!-- dark outer outline -->
      <path
        d="M7 13H11L14 8H23L26 13H28C29.7 13 31 14.3 31 16V29C31 30.7 29.7 32 28 32H7C5.3 32 4 30.7 4 29V16C4 14.3 5.3 13 7 13Z"
        fill="#22C55E"
        stroke="#0A0A0A"
        stroke-width="5"
        stroke-linejoin="round"
      />

      <!-- light inner outline -->
      <path
        d="M7 13H11L14 8H23L26 13H28C29.7 13 31 14.3 31 16V29C31 30.7 29.7 32 28 32H7C5.3 32 4 30.7 4 29V16C4 14.3 5.3 13 7 13Z"
        fill="#22C55E"
        stroke="#F5F5F5"
        stroke-width="2"
        stroke-linejoin="round"
      />

      <!-- camera lens -->
      <circle
        cx="17.5"
        cy="22"
        r="5"
        fill="#0A0A0A"
        stroke="#F5F5F5"
        stroke-width="1.5"
      />

      <circle
        cx="17.5"
        cy="22"
        r="2"
        fill="#6AB0FF"
      />

      <!-- recording/status light -->
      <circle
        cx="25"
        cy="17"
        r="1.5"
        fill="#EF4444"
        stroke="#0A0A0A"
        stroke-width="0.75"
      />

      <!-- map-point stem -->
      <path
        d="M12 32L17 37L22 32"
        fill="#22C55E"
        stroke="#0A0A0A"
        stroke-width="3"
        stroke-linejoin="round"
      />

      <path
        d="M12 32L17 37L22 32"
        fill="#22C55E"
        stroke="#F5F5F5"
        stroke-width="1"
        stroke-linejoin="round"
      />
    </svg>
  `,
});