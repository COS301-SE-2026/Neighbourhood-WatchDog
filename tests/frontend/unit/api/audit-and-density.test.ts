import { getAuditLogs } from "@/lib/api/audit";
import { fetchIncidentDensity } from "@/lib/api/incident-density";
import { apiCall } from "@/lib/api/client";

jest.mock("@/lib/api/client", () => ({
  apiCall: jest.fn(),
}));

const mockedApiCall = jest.mocked(apiCall);
const UUID = "10000000-0000-4000-8000-000000000001";
const ISO_DATE = "2026-09-30T10:00:00Z";
const auditLog = {
  id: UUID,
  user_id: UUID,
  action: "UPDATE",
  target_entity_type: "Property",
  target_entity_id: UUID,
  timestamp: ISO_DATE,
  old_values: { address: "Old address" },
  new_values: { address: "New address" },
};

describe("audit API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("requests audit logs with all filters and returns parsed data", async () => {
    const data = {
      total: 1,
      page: 2,
      size: 10,
      results: [auditLog],
    };
    mockedApiCall.mockResolvedValueOnce({
      status: 200,
      message: null,
      data,
    });

    await expect(
        getAuditLogs(2, 10, {
            searchTerm: "address change",
            action: "UPDATE",
            startDate: "2026-09-01",
            endDate: "2026-09-30",
            sortOrder: "DESC",
        }),
        ).resolves.toEqual({
        ...data,
        results: [
            {
            ...auditLog,
            timestamp: new Date("2026-09-30T10:00:00Z"),
            },
        ],
        });

    expect(mockedApiCall).toHaveBeenCalledWith(
      "/audit/get-audit-logs?page=2&size=10&search_term=address change&action=UPDATE&start_date=2026-09-01&end_date=2026-09-30&sort_order=DESC",
      { method: "GET" },
    );
  });

  it.each([
    [{ status: 400, message: "Audit logs unavailable", data: null }, "Audit logs unavailable"],
    [{ status: 400, message: null, data: null }, "No data returned"],
  ])("rejects responses without audit data", async (response, message) => {
    mockedApiCall.mockResolvedValueOnce(response);

    await expect(getAuditLogs(1, 10)).rejects.toThrow(message);
  });
});

describe("incident density API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("requests density data with the complete viewport", async () => {
    const data = {
      neighbourhood_id: "neighbourhood-1",
      start_date: "2026-09-01",
      end_date: "2026-09-30",
      cell_size_metres: 100,
      min_count: 0,
      max_count: 4,
      cells: [
        {
          cell_id: "cell-1",
          grid_x: 1,
          grid_y: 2,
          latitude: -25.7479,
          longitude: 28.2293,
          incident_count: 4,
        },
      ],
    };
    mockedApiCall.mockResolvedValueOnce({
      status: 200,
      message: null,
      data,
    });

    await expect(
      fetchIncidentDensity("neighbourhood-1", {
        startDate: "2026-09-01",
        endDate: "2026-09-30",
        west: 28,
        south: -26,
        east: 29,
        north: -25,
      }),
    ).resolves.toEqual(data);

    expect(mockedApiCall).toHaveBeenCalledWith(
      "/alerts/neighbourhoods/neighbourhood-1/incident-density?start_date=2026-09-01&end_date=2026-09-30&west=28&south=-26&east=29&north=-25",
    );
  });

  it("rejects an invalid density response", async () => {
    mockedApiCall.mockResolvedValueOnce({
      status: 200,
      message: null,
      data: { cells: [] },
    });

    await expect(
      fetchIncidentDensity("neighbourhood-1", {
        startDate: "2026-09-01",
        endDate: "2026-09-30",
        west: 28,
        south: -26,
        east: 29,
        north: -25,
      }),
    ).rejects.toThrow();
  });
});