
export function claimTrackingEvent(eventId: unknown, seenEventIds: Set<string>): boolean {
  
    if (typeof eventId !== "string" || eventId.length === 0) {
    return false;
  }

  if (seenEventIds.has(eventId)) {
    return false;
  }

  seenEventIds.add(eventId);
  return true;
  
}