/// <reference types="jest" />

import { setSession, getAccessToken, logout } from "../../../frontend/src/lib/auth/cognito";

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