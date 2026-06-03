import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import JoinNeighbourhoodPage from "@/app/joinNeighbourhood/page";
import * as api from "@/lib/api/neighbourhoodJoin";

jest.mock("@/lib/api/neighbourhoodJoin", () => ({
  submitJoinRequest: jest.fn(),
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

describe("JoinNeighbourhoodPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the form and submits a join code", async () => {
    mocked.submitJoinRequest.mockResolvedValue({
      id: "req-1",
      neighbourhood_id: "n-1",
      user_id: "u-1",
      user_name: "Test User",
      status: "PENDING",
      created_at: new Date().toISOString(),
      resolved_at: null,
    } as any);

    render(<JoinNeighbourhoodPage />);

    fireEvent.change(screen.getByLabelText(/join code/i), {
      target: { value: "north-5f3a" },
    });
    fireEvent.click(screen.getByRole("button", { name: /request to join/i }));

    await waitFor(() => {
      expect(screen.getByText(/awaiting approval/i)).toBeInTheDocument();
    });

    expect(mocked.submitJoinRequest).toHaveBeenCalledWith("NORTH-5F3A");
  });

  it("shows an error message when submit fails", async () => {
    mocked.submitJoinRequest.mockRejectedValue(
      new Error("Could not send join request."),
    );

    render(<JoinNeighbourhoodPage />);

    fireEvent.change(screen.getByLabelText(/join code/i), {
      target: { value: "X" },
    });
    fireEvent.click(screen.getByRole("button", { name: /request to join/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /could not send join request/i,
      );
    });
  });
});
