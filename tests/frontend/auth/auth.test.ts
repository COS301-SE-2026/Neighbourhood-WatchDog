import {setSession, getAccessToken, logout, login, signUp, confirmSignUp, resendConfirmationCode} from "../../../frontend/src/lib/auth/cognito";
import {getAuthHeaders, getAuthToken,} from "../../../frontend/src/lib/api/auth";

jest.mock("amazon-cognito-identity-js", () => require("../../../frontend/__mocks__/amazon-cognito-identity-js.js"));

const TEST_ID_TOKEN =
  "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwibmFtZSI6IlRlc3QgVXNlciIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.test-signature";

describe("setSession", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("stores tokens in localStorage", () => {
    setSession({
      accessToken: "access123",
      idToken: TEST_ID_TOKEN,
    });

    expect(localStorage.getItem("accessToken")).toBe("access123");
    expect(localStorage.getItem("idToken")).toBe(TEST_ID_TOKEN);
  });
});

test("returns stored access token", () => {
  localStorage.setItem("accessToken", "abc123");
  expect(getAccessToken()).toBe("abc123");
});

test("clears localStorage", () => {
  localStorage.setItem("accessToken", "abc");
  localStorage.setItem("idToken", "xyz");

  logout();

  expect(localStorage.getItem("accessToken")).toBeNull();
  expect(localStorage.getItem("idToken")).toBeNull();
});
//LOGIN//////////////////////////////////////////////////////
test("login returns access and id tokens", async () => {
  (fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({
      data: {
        access_token: "mock-access-token",
        id_token: "mock-id-token",
        expires_in: 3600,
      },
    }),
  });

  const result = await login("test@example.com", "Password123!");

  expect(result).toEqual({
    accessToken: "mock-access-token",
    idToken: "mock-id-token",
    expiresIn: 3600,
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
//END LOGIN//////////////////////////////////////////////////////





//SIGNUP/////////////////////////////////////////////////////////
test("signup returns created user", async () => {
  (fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({
      user_sub: "user-123",
      confirmed: false,
    }),
  });

  const result = await signUp(
    "test@example.com",
    "Password123!",
    "Test User",
    "123 Main Street"
  );

  expect(result).toEqual({
    userSub: "user-123",
    confirmed: false,
  });
});

test("signup throws nested backend error message", async () => {// remove if you want less errors
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
      "Test User",
      "123 Main Street"
    )
  ).rejects.toThrow("User already exists");
});
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

  expect(getAuthHeaders()).toEqual({
    "Content-Type": "application/json",
    Authorization: "Bearer token123",
  });
});
// GET AUTH HEADERS/////////////////