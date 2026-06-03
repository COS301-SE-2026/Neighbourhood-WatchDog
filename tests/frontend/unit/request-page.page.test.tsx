import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import JoinRequestsPage from "@/app/request-page/page";
import * as api from "@/lib/api/neighbourhoodJoin";
import { mockJoinRequest } from "../fixtures/joinRequest";

jest.mock("@/lib/api/neighbourhoodJoin", () => ({
  fetchJoinRequests: jest.fn(),
  resolveJoinRequest: jest.fn(),
  ApiError: class ApiError extends Error {
    statusCode?: number;

    constructor(message: string, statusCode?: number) {
      super(message);
      this.name = "ApiError";
      this.statusCode = statusCode;
    }
  },
}));

const mocked = api as jest.Mocked<typeof api>;

describe("JoinRequestsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads requests and allows approval", async () => {
    mocked.fetchJoinRequests.mockResolvedValue([mockJoinRequest] as any);
    mocked.resolveJoinRequest.mockResolvedValue({
      ...mockJoinRequest,
      status: "APPROVED",
    } as any);

    render(<JoinRequestsPage />);

    expect(await screen.findByText(/join requests/i)).toBeInTheDocument();

    const approve = await screen.findByRole("button", {
      name: /approve join request/i,
    });
    fireEvent.click(approve);

    await waitFor(() => {
      expect(mocked.resolveJoinRequest).toHaveBeenCalledWith(
        mockJoinRequest.id,
        "APPROVE",
      );
    });
  });

  it("shows an error banner when fetch fails", async () => {
    mocked.fetchJoinRequests.mockRejectedValue(new Error("Network"));

    render(<JoinRequestsPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/network/i);
    });
  });
});
