import {
  act,
  renderHook,
  waitFor,
} from "@testing-library/react";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import type {
  ReactNode,
} from "react";

import {
  getNeighbourhoodMapProperties,
} from "@/lib/api/neighbourhood";

import {
  useNeighbourhoodMapProperties,
} from "@/hooks/use-neighbourhood-map-properties";

import type {
  NeighbourhoodMapProperty,
} from "@/lib/validators/neighbourhood";

jest.mock("@/lib/api/neighbourhood", () => ({
  getNeighbourhoodMapProperties: jest.fn(),
}));

const mockGetProperties =
  getNeighbourhoodMapProperties as jest.MockedFunction<
    typeof getNeighbourhoodMapProperties
  >;

const properties: NeighbourhoodMapProperty[] = [
  {
    id: "property-1",
    address: "12 Main Street",
    property_type: "PRIVATE",
    latitude: -25.7479,
    longitude: 28.2293,
  },
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function QueryWrapper({
    children,
  }: {
    children: ReactNode;
  }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe("useNeighbourhoodMapProperties", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("loads neighbourhood properties", async () => {
    mockGetProperties.mockResolvedValue(properties);

    const { result } = renderHook(
      () =>
        useNeighbourhoodMapProperties(
          "neighbourhood-1",
          true,
        ),
      {
        wrapper: createWrapper(),
      },
    );

    await waitFor(() => {
      expect(result.current.properties).toEqual(
        properties,
      );
    });

    expect(
      mockGetProperties,
    ).toHaveBeenCalledWith("neighbourhood-1");

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("returns the API error message", async () => {
    mockGetProperties.mockRejectedValue(
      new Error("Network down"),
    );

    const { result } = renderHook(
      () =>
        useNeighbourhoodMapProperties(
          "neighbourhood-1",
          true,
        ),
      {
        wrapper: createWrapper(),
      },
    );

    await waitFor(() => {
      expect(result.current.error).toBe(
        "Network down",
      );
    });

    expect(result.current.properties).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  test("does not request data when disabled", () => {
    renderHook(
      () =>
        useNeighbourhoodMapProperties(
          "neighbourhood-1",
          false,
        ),
      {
        wrapper: createWrapper(),
      },
    );

    expect(
      mockGetProperties,
    ).not.toHaveBeenCalled();
  });

  test("allows a failed request to be retried", async () => {
    mockGetProperties
      .mockRejectedValueOnce(
        new Error("Temporary failure"),
      )
      .mockResolvedValueOnce(properties);

    const { result } = renderHook(
      () =>
        useNeighbourhoodMapProperties(
          "neighbourhood-1",
          true,
        ),
      {
        wrapper: createWrapper(),
      },
    );

    await waitFor(() => {
      expect(result.current.error).toBe(
        "Temporary failure",
      );
    });

    await act(async () => {
      await result.current.retry();
    });

    await waitFor(() => {
      expect(result.current.properties).toEqual(
        properties,
      );
    });
  });
});