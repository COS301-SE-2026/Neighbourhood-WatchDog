/// <reference types="jest" />

// Apply mock before importing the module under test so the mock is used during
// module initialization (the code creates CognitoUserPool at module load).
// Explicitly load the manual mock file so Jest uses it for the Cognito module
jest.mock("amazon-cognito-identity-js", () => require("../../../frontend/__mocks__/amazon-cognito-identity-js.js"));
// Require the module after mocking so the manual mock in __mocks__ is used
const { setSession, getAccessToken, logout, login, signUp } = require("../../../frontend/src/lib/auth/cognito");


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
  // The manual mock returns an object like { username: email }
  expect(result).toHaveProperty('username', 'test@example.com');
});