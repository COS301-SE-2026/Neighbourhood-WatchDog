import { claimTrackingEvent } from "../../../frontend/src/lib/tracking-events";

describe("claimTrackingEvent", () => {
  test("claims a new event exactly once", () => {
    const seen = new Set<string>();

    expect(claimTrackingEvent("sighting-1", seen)).toBe(true);
    expect(claimTrackingEvent("sighting-1", seen)).toBe(false);
    expect(seen).toEqual(new Set(["sighting-1"]));
  });

  test("allows different event IDs", () => {
    const seen = new Set<string>();

    expect(claimTrackingEvent("sighting-1", seen)).toBe(true);
    expect(claimTrackingEvent("sighting-2", seen)).toBe(true);
    expect(seen).toEqual(
      new Set(["sighting-1", "sighting-2"]),
    );
  });

  test("rejects missing or malformed event IDs", () => {
    const seen = new Set<string>();

    expect(claimTrackingEvent(undefined, seen)).toBe(false);
    expect(claimTrackingEvent(null, seen)).toBe(false);
    expect(claimTrackingEvent("", seen)).toBe(false);
    expect(claimTrackingEvent(123, seen)).toBe(false);
    expect(seen.size).toBe(0);
  });
});