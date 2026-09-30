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


});
