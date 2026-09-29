import {
  dispatchRouteUrl,
} from "@/components/shared/DispatchRequestPopup";

test("builds a route to the dispatched property", () => {
  expect(
    dispatchRouteUrl("neighbourhood-1", "sighting-property-2"),
  ).toBe(
    "/dashboard/neighbourhood/neighbourhood-1/map" +
      "?routePropertyId=sighting-property-2",
  );
});
