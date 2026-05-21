// Minimal manual mock for amazon-cognito-identity-js used by tests
class CognitoUserPool {
  constructor() {}
  signUp(email, password, attributes, validationData, callback) {
    // simulate success (synchronous for tests)
    callback(null, { user: { username: email } });
  }
}

class CognitoUserAttribute {
  constructor(obj) {
    this.Name = obj?.Name;
    this.Value = obj?.Value;
  }
}

class AuthenticationDetails {
  constructor(obj) {
    this.Username = obj?.Username;
    this.Password = obj?.Password;
  }
}

class CognitoUser {
  constructor({ Username } = {}) {
    this.Username = Username;
  }

  authenticateUser(authDetails, callbacks) {
    // simulate successful authentication (synchronous for tests)
    const result = {
      getAccessToken: () => ({ getJwtToken: () => 'mock-access-token' }),
      getIdToken: () => ({ getJwtToken: () => 'mock-id-token' }),
    };
    if (callbacks && typeof callbacks.onSuccess === 'function') {
      callbacks.onSuccess(result);
    }
  }
}

module.exports = {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
};
