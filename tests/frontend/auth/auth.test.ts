/// <reference types="jest" />

import { setSession, getAccessToken, logout, login, signUp } from "../../../frontend/src/lib/auth/cognito";
jest.mock("amazon-cognito-identity-js");
//TEST SET SESSION
describe("setSession", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("stores tokens in localStorage", () => {
    setSession({
      accessToken: "access123",
      idToken: "id123",
    });

    expect(localStorage.getItem("accessToken")).toBe("access123");
    expect(localStorage.getItem("idToken")).toBe("id123");
  });
});

//TEST GET ACCESS TOKEN
test("returns stored access token", () => {
  localStorage.setItem("accessToken", "abc123");

  expect(getAccessToken()).toBe("abc123");
});

//TEST LOGOUT
test("clears localStorage", () => {
  localStorage.setItem("accessToken", "abc");
  localStorage.setItem("idToken", "xyz");

  logout();

  expect(localStorage.getItem("accessToken")).toBeNull();
  expect(localStorage.getItem("idToken")).toBeNull();
});

test("login returns access and id tokens", async () => {
  const result = await login(
    "test@example.com",
    "Password123!"
  );

  expect(result).toEqual({
    accessToken: "mock-access-token",
    idToken: "mock-id-token",
  });
});

test("signup returns created user", async () => {
  const result = await signUp(
    "test@example.com",
    "Password123!",
    "Test User",
    "123 Main Street"
  );

  expect(result).toBeDefined();
});