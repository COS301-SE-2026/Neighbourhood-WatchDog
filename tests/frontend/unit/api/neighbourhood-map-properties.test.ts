import {
  getNeighbourhoodMapProperties,
} from "@/lib/api/neighbourhood";

import {
  apiCall,
} from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockApiCall =
  apiCall as jest.MockedFunction<typeof apiCall>;

const properties = [
  {
    id: "property-1",
    address: "12 Main Street",
    property_type: "PRIVATE" as const,
    latitude: -25.7479,
    longitude: 28.2293,
  },
  {
    id: "property-2",
    address: "Unknown Location",
    property_type: "PUBLIC" as const,
    latitude: null,
    longitude: null,
  },
];

describe("getNeighbourhoodMapProperties", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("requests all properties for a neighbourhood", async () => {
    mockApiCall.mockResolvedValue(properties);

    const result =
      await getNeighbourhoodMapProperties(
        "neighbourhood/one",
      );

    expect(mockApiCall).toHaveBeenCalledWith(
      "/neighbourhood/neighbourhood%2Fone/map/properties",
      {
        method: "GET",
      },
    );

    expect(result).toEqual(properties);
  });

  test("rejects invalid coordinates", async () => {
    mockApiCall.mockResolvedValue([
      {
        id: "property-1",
        address: "Invalid Property",
        property_type: "PRIVATE",
        latitude: 91,
        longitude: 28.2293,
      },
    ]);

    await expect(
      getNeighbourhoodMapProperties(
        "neighbourhood-1",
      ),
    ).rejects.toThrow();
  });
});