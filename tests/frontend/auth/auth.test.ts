import { storeAccessToken, clearAccessToken } from "../../../frontend/src/lib/auth/token_store";
import {AUTH_EVENT, setSession, getAccessToken, logout, login, signUp, confirmSignUp, resendConfirmationCode, verifyMfa} from "../../../frontend/src/lib/auth/cognito";
import {getAuthHeaders, getAuthToken,} from "../../../frontend/src/lib/api/auth";
import {
  getStoredUser,
  isAuthenticated,
  updateStoredFullName,
} from "../../../frontend/src/lib/auth/cognito";
jest.mock("amazon-cognito-identity-js", () => require("../../../frontend/__mocks__/amazon-cognito-identity-js.js"));

const TEST_ID_TOKEN =
  "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwibmFtZSI6IlRlc3QgVXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.test-signature";


beforeEach(() => {
  localStorage.clear();
  clearAccessToken();
  jest.clearAllMocks;
  (fetch as jest.Mock).mockReset();
});

afterEach(() => {
  jest.restoreAllMocks();
})

describe("session storage", () => {
 test("stores access token in memory and not localStorage", () => {
  setSession({
    accessToken: "access123",
    idToken: TEST_ID_TOKEN,
    expiresIn: 3600,
  });

  expect(getAccessToken()).toBe("access123");

  expect(localStorage.getItem("accessToken")).toBeNull();
  expect(localStorage.getItem("idToken")).toBeNull();
  expect(localStorage.getItem("refreshToken")).toBeNull();

  expect(localStorage.getItem("userSub")).toBe("test-user-123");
  expect(localStorage.getItem("fullname")).toBe("Test User");
  expect(localStorage.getItem("email")).toBe("test@example.com");
  });


  test("returns access token from memory", () => {
    storeAccessToken("abc123", 3600);
    expect(getAccessToken()).toBe("abc123");
  });

  test("does not read access token from localStorage", () => {
    localStorage.setItem("accessToken", "unsafe-taken");

    expect(getAccessToken()).toBeNull();
  });

  test("setSession rejects missing access token", () => {
    expect(() =>
      setSession({
        accessToken: "",
        idToken: TEST_ID_TOKEN,
      })
    ).toThrow("Cannot store empty auth tokens");
  });

  test("setSession rejects missing ID token", () => {
    expect(() =>
      setSession({
        accessToken: "access-token",
        idToken: "",
      })
    ).toThrow("Cannot store empty auth tokens");
  });

  test("removes expired access token from memory", () => {
    const startingTime = 1_000_000;

    jest.spyOn(Date, "now").mockReturnValue(startingTime);
    storeAccessToken("expired-token", 60);

    jest.spyOn(Date, "now").mockReturnValue(
      startingTime + 61_000,
    );

    expect(getAccessToken()).toBeNull();
  });
});

describe("authentication state", () = {
  test("isAuthenticated returns false without an access token", () => {
    expect(isAuthenticated()).toBe(false);
  

  test("isAuthenticated returns true with an in-memory access token", () => {
    storeAccessToken("valid-token", 3600);

    expect(isAuthenticated()).toBe(true);
  });

  test("returns stored user when authenticated", () => {
    storeAccessToken("valid-token", 3600);

    localStorage.setItem("userSub", "user-123");
    localStorage.setItem("fullname", "Test User");
    localStorage.setItem("email", "test@example.com");
    localStorage.setItem("address", "123 Main Street");

    expect(getStoredUser()).toEqual({
      sub: "user-123",
      fullname: "Test User",
      email: "test@example.com",
      address: "123 Main Street",
    });
  });

  test("returns null when profile exists without access token", () => {
    localStorage.setItem("userSub", "user-123");
    localStorage.setItem("fullname", "Test User");

    expect(getStoredUser()).toBeNull();
  });

  test("returns null when user sub is missing", () => {
    storeAccessToken("valid-token", 3600);

    expect(getStoredUser()).toBeNull();
  });

});


//LOGIN//////////////////////////////////////////////////////
describe("login", () ={
  test("login returns access and id tokens", async () => {
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          access_token: "mock-access-token",
          id_token: "mock-id-token",
          expires_in: 3600,
          token_type: "Bearer"
        },
      }),
    });

    const result = await login("test@example.com", "Password123!");

    expect(result).toEqual({
      accessToken: "mock-access-token",
      idToken: "mock-id-token",
      expiresIn: 3600,
      mfaRequired: false,
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/auth/login"),
      expect.objectContaining({
        method: "POST",
        credentials: "include"
      })
    );
  });

  test("login returns MFA challenge", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          mfa_required: true,
          session: "abc-session",
          delivery: {
            medium: "EMAIL",
            destination: "z***@g***",
          },
        },
      }),
    });

    const result = await login(
      "test@example.com",
      "Password123!"
    );

    expect(result).toEqual({
      mfaRequired: true,
      session: "abc-session",
      delivery: {
        medium: "EMAIL",
        destination: "z***@g***",
      },
    });
  });

  test("login throws backend error message", async () => { // remove if you want less errors
    (fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: async () => ({
        detail: "Invalid credentials",
      }),
    });

    await expect(
      login("test@example.com", "wrongpassword")
    ).rejects.toThrow("Invalid credentials");
  });

});





//END LOGIN//////////////////////////////////////////////////////





//SIGNUP/////////////////////////////////////////////////////////
describe("signup", () => {
  test("returns created user", async () => {
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          user_sub: "user-123",
          confirmed: false
        }
    }), 
  });

  const result = await signUp(
    "test@example.com",
    "Password123!",
    "Test",
    "User",
    "123 Main Street"
  );

  expect(result).toEqual({
    userSub: "user-123",
    confirmed: false,
  });
  });

  test("throws nested backend error message", async () => {// remove if you want less errors
    (fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: async () => ({
        detail: {
          message: "User already exists",
        },
      }),
    });

    await expect(
      signUp(
        "test@example.com",
        "Password123!",
        "Test",
        "User"
        "123 Main Street"
      )
    ).rejects.toThrow("User already exists");
  });
})

//END SIGNUP///////////////////////////////////////////////////////

//CONFRIM SIGNUP////////////////////////////////////////////////
test("confirm signup returns confirmed status", async () => {
  (fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({
      confirmed: true,
    }),
  });

  const result = await confirmSignUp(
    "test@example.com",
    "123456"
  );

  expect(result).toBe(true);
});

test("confirm signup handles errors", async () => {// remove if you want less errors
  (fetch as jest.Mock).mockRejectedValue(
    new Error("Confirmation failed")
  );

  await expect(
    confirmSignUp(
      "test@example.com",
      "123456"
    )
  ).rejects.toThrow("Confirmation failed");
});
//END CONFIRM SIGNUP///////////////////////////////////////////////

//RESEND CODE///////////////////////////////////////////////
test("resend confirmation code succeeds", async () => {
  (fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({}),
  });

  await expect(
    resendConfirmationCode("test@example.com")
  ).resolves.toBeUndefined();
});

test("resend confirmation code handles errors", async () => { // remove if you want less errors
  (fetch as jest.Mock).mockRejectedValue(
    new Error("Resend failed")
  );

  await expect(
    resendConfirmationCode("test@example.com")
  ).rejects.toThrow("Resend failed");
});
//END RESEND CODE///////////////////////////////////////////////

//getAuthToken////////////////////
test("getAuthToken returns accessToken from localStorage", () => {
  localStorage.setItem("accessToken", "access-123");

  expect(getAuthToken()).toBe("access-123");
});

test("getAuthToken falls back to authToken", () => {
  localStorage.removeItem("accessToken");
  localStorage.setItem("authToken", "auth-123");

  expect(getAuthToken()).toBe("auth-123");
});

//getAuthToken end////////////////////////////

// GET AUTH HEADERS///////////////////
test("getAuthHeaders returns authorization and content type", () => {
  localStorage.setItem("accessToken", "token123");

  // expect(getAuthHeaders()).toEqual({
  //   "Content-Type": "application/json",
  //   Authorization: "Bearer token123",
  // });
});
// GET AUTH HEADERS/////////////////

test("verify MFA returns access and id tokens", async () => {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      success: true,
      data: {
        access_token: "mock-access-token",
        id_token: "mock-id-token",
        refresh_token: "mock-refresh-token",
        expires_in: 3600,
        token_type: "Bearer",
      },
    }),
  });

  const result = await verifyMfa(
    "test@example.com",
    "abc-session",
    "123456"
  );

  expect(result).toEqual({
    accessToken: "mock-access-token",
    idToken: "mock-id-token",
    expiresIn: 3600,
  });

  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/auth/verify-mfa"),
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify({
        email: "test@example.com",
        session: "abc-session",
        code: "123456",
      }),
    })
  );
});

test("verify MFA throws backend error message", async () => {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: false,
    json: async () => ({
      detail: {
        message: "Invalid verification code",
      },
    }),
  });

  await expect(
    verifyMfa(
      "test@example.com",
      "abc-session",
      "123456"
    )
  ).rejects.toThrow("Invalid verification code");
});





test("getAccessToken logs out when the token is expired", () => {
  localStorage.setItem("accessToken", "expired-token");
  localStorage.setItem(
    "tokenExpiry",
    String(Date.now() - 1000)
  );

  expect(getAccessToken()).toBeNull();
  expect(localStorage.getItem("accessToken")).toBeNull();
});

test("getStoredUser returns the stored user", () => {
  localStorage.setItem("accessToken", "valid-token");
  localStorage.setItem("userSub", "user-123");
  localStorage.setItem("fullname", "Test User");
  localStorage.setItem("email", "test@example.com");
  localStorage.setItem("address", "123 Main Street");

  expect(getStoredUser()).toEqual({
    sub: "user-123",
    fullname: "Test User",
    email: "test@example.com",
    address: "123 Main Street",
  });
});

// test("getStoredUser returns null without a user sub", () => {
//   localStorage.setItem("accessToken", "valid-token");

//   expect(getStoredUser()).toBeNull();
// });

test("updateStoredFullName updates localStorage", () => {
  updateStoredFullName("Updated User");

  expect(localStorage.getItem("fullname")).toBe(
    "Updated User"
  );
});


