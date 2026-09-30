import { act, cleanup, renderHook, waitFor } from "@testing-library/react";

import { ApiError, apiFetch } from "@/lib/api/alert";
import { useClip } from "@/hooks/use-clip";

jest.mock("@/lib/api/alert", () => ({
  apiFetch: jest.fn(),
  ApiError: class extends Error {
    constructor(
      message: string,
      public statusCode?: number,
    ) {
      super(message);
    }
  },
}));

const mockApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;
const readyClip = {
  url: "https://example.test/clip.mp4",
  expires_in: 60,
};

describe("useClip", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
    jest.useRealTimers();
  });

  test("stays idle without a clip ID", async () => {
    const { result } = renderHook(() => useClip(null));

    expect(result.current.status).toBe("idle");

    await act(async () => {
      await result.current.loadClip();
    });

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  test("loads an alert clip and permits manual reload", async () => {
    mockApiFetch.mockResolvedValue(readyClip);
    const { result } = renderHook(() => useClip("alert-1"));

    await waitFor(() => {
      expect(result.current.status).toBe("ready");
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/api/clips/alert-1");
    expect(result.current.url).toBe(readyClip.url);

    await act(async () => {
      await result.current.loadClip();
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
  });

  test("uses the tracking-sighting endpoint", async () => {
    mockApiFetch.mockResolvedValue(readyClip);
    const { result } = renderHook(() =>
      useClip("sighting-1", "tracking-sighting"),
    );

    await waitFor(() => {
      expect(result.current.status).toBe("ready");
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/clips/tracking/sightings/sighting-1/clip",
    );
  });

  test.each([
    [410, "expired", "The clip has expired"],
    [403, "forbidden", "You do not have permission to view this footage"],
    [503, "unavailable", "Clip storage is unavailable."],
    [500, "error", "Failed to load footage"],
  ] as const)("maps HTTP %i to %s", async (code, status, message) => {
    mockApiFetch.mockRejectedValue(new ApiError("Request failed", code));
    const { result } = renderHook(() => useClip("alert-1"));

    await waitFor(() => {
      expect(result.current.status).toBe(status);
    });

    expect(result.current.errorMessage).toBe(message);
    expect(mockApiFetch).toHaveBeenCalledTimes(1);
  });

  test("shows a generic error for a network failure", async () => {
    mockApiFetch.mockRejectedValue(new Error("Network failed"));
    const { result } = renderHook(() => useClip("alert-1"));

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });

    expect(result.current.errorMessage).toBe("Failed to load footage");
  });

  test("retries a processing clip and then displays it", async () => {
    jest.useFakeTimers();
    mockApiFetch
      .mockRejectedValueOnce(new ApiError("Processing", 404))
      .mockResolvedValueOnce(readyClip);

    const { result } = renderHook(() => useClip("alert-1"));

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.status).toBe("processing");

    await act(async () => {
      jest.advanceTimersByTime(5_000);
      await Promise.resolve();
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
    expect(result.current.status).toBe("ready");
    expect(result.current.url).toBe(readyClip.url);
  });

  test("stops after ten processing responses", async () => {
    jest.useFakeTimers();
    mockApiFetch.mockRejectedValue(new ApiError("Processing", 404));

    const { result } = renderHook(() => useClip("alert-1"));

    await act(async () => {
      await Promise.resolve();
    });

    for (let attempt = 1; attempt < 10; attempt += 1) {
      await act(async () => {
        jest.advanceTimersByTime(5_000);
        await Promise.resolve();
      });
    }

    expect(mockApiFetch).toHaveBeenCalledTimes(10);
    expect(result.current.status).toBe("unavailable");
    expect(result.current.errorMessage).toBe(
      "Footage was not available after processing.",
    );
  });

  test("cancels a scheduled retry on unmount", async () => {
    jest.useFakeTimers();
    mockApiFetch.mockRejectedValue(new ApiError("Processing", 404));

    const { unmount } = renderHook(() => useClip("alert-1"));

    await act(async () => {
      await Promise.resolve();
    });

    unmount();

    await act(async () => {
      jest.advanceTimersByTime(5_000);
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
  });


});
