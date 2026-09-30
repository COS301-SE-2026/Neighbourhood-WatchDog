import {
  addNeighbourhood,
  getNeighbourhood,
  getNeighbourhoodMapProperties,
  getNeighbourhoodMembers,
  getNeighbourhoodPropertyDetails,
  getNeighbourhoods,
  getSecurityAvailability,
  joinNeighbourhood,
  leaveNeighbourhood,
  updateNeighbourhoodMemberRole,
  updateSecurityAvailability,
  updateSecurityLocation,
} from "@/lib/api/neighbourhood";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);
const NEIGHBOURHOOD_ID = "10000000-0000-4000-8000-000000000001";
const PROPERTY_ID = "10000000-0000-4000-8000-000000000002";
const USER_ID = "10000000-0000-4000-8000-000000000003";
const neighbourhood = {
  id: NEIGHBOURHOOD_ID,
  name: "Central neighbourhood",
  location: "Pretoria",
  join_code: "ABC123",
  created_at: "2026-09-30T10:00:00Z",
};
const member = {
  user_id: USER_ID,
  first_name: "Test",
  last_name: "Member",
  email: "member@example.com",
  role: "RESIDENT",
};
const mapProperties = [
  {
    id: PROPERTY_ID,
    address: "1 Main Street",
    property_type: "PRIVATE",
    latitude: -25.7479,
    longitude: 28.2293,
  },
];

describe("neighbourhood API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("creates a neighbourhood and returns its data", async () => {
    const input = {
      name: "Central neighbourhood",
      location: "Pretoria",
      property_id: PROPERTY_ID,
    };
    mockedApiCall.mockResolvedValueOnce({ status: 201, data: neighbourhood });

    await expect(addNeighbourhood(input)).resolves.toEqual(neighbourhood);
    expect(mockedApiCall).toHaveBeenCalledWith(
      "/neighbourhood/create-neighbourhood",
      { method: "POST", body: input },
    );
  });

  it("rejects a neighbourhood response without data", async () => {
    mockedApiCall.mockResolvedValueOnce({
      status: 400,
      message: "Neighbourhood was not created",
    });

    await expect(
      addNeighbourhood({
        name: "Central neighbourhood",
        location: "Pretoria",
        property_id: PROPERTY_ID,
      }),
    ).rejects.toThrow("Neighbourhood was not created");
  });

  it("gets neighbourhood collections and individual records", async () => {
    mockedApiCall
      .mockResolvedValueOnce([neighbourhood])
      .mockResolvedValueOnce(neighbourhood)
      .mockResolvedValueOnce(neighbourhood);

    await expect(getNeighbourhoods()).resolves.toEqual([neighbourhood]);
    await expect(getNeighbourhood(NEIGHBOURHOOD_ID)).resolves.toEqual(
      neighbourhood,
    );
    await expect(joinNeighbourhood("ABC123")).resolves.toEqual(neighbourhood);

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      3,
      "/neighbourhood/join",
      { method: "POST", body: { join_code: "ABC123" } },
    );
  });

  it("gets property details and map properties", async () => {
    mockedApiCall
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(mapProperties);

    await expect(getNeighbourhoodPropertyDetails()).resolves.toEqual([]);
    await expect(
      getNeighbourhoodMapProperties("neighbourhood/one"),
    ).resolves.toEqual(mapProperties);

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      2,
      "/neighbourhood/neighbourhood%2Fone/map/properties",
      { method: "GET" },
    );
  });

  it("rejects invalid map-property data", async () => {
    mockedApiCall.mockResolvedValueOnce([
      {
        id: PROPERTY_ID,
        address: "Invalid coordinates",
        property_type: "PRIVATE",
        latitude: 91,
        longitude: 28.2293,
      },
    ]);

    await expect(
      getNeighbourhoodMapProperties(NEIGHBOURHOOD_ID),
    ).rejects.toThrow();
  });

  it("gets members and updates a member role", async () => {
    mockedApiCall
      .mockResolvedValueOnce([member])
      .mockResolvedValueOnce({
        status: 200,
        message: "Updated",
        data: { ...member, role: "SECURITY_OFFICER" },
      });

    await expect(getNeighbourhoodMembers(NEIGHBOURHOOD_ID)).resolves.toEqual([
      member,
    ]);
    await expect(
      updateNeighbourhoodMemberRole(NEIGHBOURHOOD_ID, USER_ID, {
        role: "SECURITY_OFFICER",
      }),
    ).resolves.toEqual({ ...member, role: "SECURITY_OFFICER" });
  });

  it("rejects a member-role update without data", async () => {
    mockedApiCall.mockResolvedValueOnce({
      status: 400,
      message: "Role update failed",
    });

    await expect(
      updateNeighbourhoodMemberRole(NEIGHBOURHOOD_ID, USER_ID, {
        role: "RESIDENT",
      }),
    ).rejects.toThrow("Role update failed");
  });

  it("leaves a neighbourhood after validating both IDs", async () => {
    mockedApiCall.mockResolvedValueOnce(undefined);

    await expect(
      leaveNeighbourhood({
        neighbourhoodId: NEIGHBOURHOOD_ID,
        propertyId: PROPERTY_ID,
      }),
    ).resolves.toBeUndefined();

    expect(mockedApiCall).toHaveBeenCalledWith(
      `/neighbourhood/${NEIGHBOURHOOD_ID}/properties/${PROPERTY_ID}/leave`,
      { method: "PATCH" },
    );
  });

  it("rejects invalid leave parameters before making a request", async () => {
    await expect(
      leaveNeighbourhood({
        neighbourhoodId: "not-a-uuid",
        propertyId: PROPERTY_ID,
      } as never),
    ).rejects.toThrow();
    expect(mockedApiCall).not.toHaveBeenCalled();
  });

  it("updates security availability and location", async () => {
    mockedApiCall
      .mockResolvedValueOnce({ status: 200, message: null })
      .mockResolvedValueOnce({ status: 200, message: null });

    await expect(
      updateSecurityAvailability(NEIGHBOURHOOD_ID, "ON_DUTY"),
    ).resolves.toEqual({ status: 200, message: null });
    await expect(
      updateSecurityLocation({
        neighbourhood_id: NEIGHBOURHOOD_ID,
        latitude: -25.7479,
        longitude: 28.2293,
      }),
    ).resolves.toEqual({ status: 200, message: null });
  });

  it("gets security availability", async () => {
    const availability = {
      status: 200,
      message: null,
      availability: "AVAILABLE",
      location_updated_at: "2026-09-30T10:00:00Z",
    };
    mockedApiCall.mockResolvedValueOnce(availability);

    await expect(
      getSecurityAvailability(NEIGHBOURHOOD_ID),
    ).resolves.toEqual(availability);
  });
});