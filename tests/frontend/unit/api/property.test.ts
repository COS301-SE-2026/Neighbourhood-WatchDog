import {
  addProperty,
  getPropertyDetails,
  getPropertyMembers,
  getPropertyResidentContext,
  invitePropertyMember,
  removeProperty,
  removePropertyMember,
} from "@/lib/api/property";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);
const PROPERTY_ID = "10000000-0000-4000-8000-000000000001";
const USER_ID = "10000000-0000-4000-8000-000000000002";
const property = {
  property_id: PROPERTY_ID,
  neighbourhood_id: null,
  address: "1 Main Street",
  property_type: "PRIVATE",
  latitude: -25.7479,
  longitude: 28.2293,
  created_at: "2026-09-30T10:00:00Z",
};
const member = {
  user_id: USER_ID,
  first_name: "Test",
  last_name: "Resident",
  email: "resident@example.com",
  is_admin: false,
};
const residentContext = {
  property_id: PROPERTY_ID,
  address: "1 Main Street",
  property_type: "PRIVATE",
  neighbourhood_id: null,
  latitude: -25.7479,
  longitude: 28.2293,
  created_at: "2026-09-30T10:00:00Z",
  residents: [member],
};

describe("property API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("creates a property and returns its data", async () => {
    const input = {
      address: "1 Main Street",
      property_type: "PRIVATE",
      latitude: -25.7479,
      longitude: 28.2293,
    } as never;
    mockedApiCall.mockResolvedValueOnce({ status: 201, data: property });

    await expect(addProperty(input)).resolves.toEqual(property);
    expect(mockedApiCall).toHaveBeenCalledWith(
      "/properties/create-property",
      { method: "POST", body: input },
    );
  });

  it("rejects property creation without data", async () => {
    mockedApiCall.mockResolvedValueOnce({
      status: 400,
      message: "Property was not created",
    });

    await expect(addProperty({} as never)).rejects.toThrow(
      "Property was not created",
    );
  });

  it("gets property details and members", async () => {
    mockedApiCall
      .mockResolvedValueOnce(property)
      .mockResolvedValueOnce({ members: [member] });

    await expect(getPropertyDetails(PROPERTY_ID)).resolves.toEqual(property);
    await expect(getPropertyMembers(PROPERTY_ID)).resolves.toEqual({
      members: [member],
    });
  });

  it("parses resident context", async () => {
    mockedApiCall.mockResolvedValueOnce(residentContext);

    await expect(getPropertyResidentContext(PROPERTY_ID)).resolves.toEqual({
        ...residentContext,
        created_at: new Date("2026-09-30T10:00:00Z"),
    });
  });

  it("rejects an invalid resident context", async () => {
    mockedApiCall.mockResolvedValueOnce({ property_id: PROPERTY_ID });

    await expect(getPropertyResidentContext(PROPERTY_ID)).rejects.toThrow();
  });

  it("invites a property member", async () => {
    const input = { email: "new-member@example.com" } as never;
    const response = { message: "Invitation sent", email_sent: true };
    mockedApiCall.mockResolvedValueOnce(response);

    await expect(invitePropertyMember(PROPERTY_ID, input)).resolves.toEqual(
      response,
    );
    expect(mockedApiCall).toHaveBeenCalledWith(
      `/properties/${PROPERTY_ID}/member`,
      { method: "POST", body: input },
    );
  });

  it("removes a member and removes a property", async () => {
    mockedApiCall
      .mockResolvedValueOnce(undefined)
      .mockResolvedValueOnce(undefined);

    await expect(
      removePropertyMember(PROPERTY_ID, USER_ID),
    ).resolves.toBeUndefined();
    await expect(removeProperty(PROPERTY_ID)).resolves.toBeUndefined();

    expect(mockedApiCall).toHaveBeenNthCalledWith(
      1,
      `/properties/${PROPERTY_ID}/members/${USER_ID}`,
      { method: "DELETE" },
    );
    expect(mockedApiCall).toHaveBeenNthCalledWith(
      2,
      `/properties/${PROPERTY_ID}`,
      { method: "DELETE" },
    );
  });
});