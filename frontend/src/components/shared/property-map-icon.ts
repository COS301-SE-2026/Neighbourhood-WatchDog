import { divIcon } from "leaflet";

export const PROPERTY_MAP_ICON = divIcon({
  className: "watchdog-property-icon",
  iconSize: [32, 36],
  iconAnchor: [16, 36],
  popupAnchor: [0, -36],
  html: `
    <svg
      class="watchdog-property-icon__svg"
      width="32"
      height="36"
      viewBox="0 0 32 36"
      role="img"
      aria-label="Property"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title>Property</title>

      <!-- dark outer outline for visibility -->
      <path
        d="M4 14L16 4L28 14V30H4V14Z"
        fill="#2563EB"
        stroke="#0A0A0A"
        stroke-width="5"
        stroke-linejoin="round"
      />

      <!-- light inner outline -->
      <path
        d="M4 14L16 4L28 14V30H4V14Z"
        fill="#2563EB"
        stroke="#F5F5F5"
        stroke-width="2"
        stroke-linejoin="round"
      />

      <!-- door -->
      <path
        d="M13 30V20H19V30"
        fill="#0A0A0A"
        stroke="#F5F5F5"
        stroke-width="1.5"
      />

      <!-- window -->
      <path
        d="M10 15H14V19H10V15ZM18 15H22V19H18V15Z"
        fill="#BFDBFE"
        stroke="#0A0A0A"
        stroke-width="1"
      />
    </svg>
  `,
});