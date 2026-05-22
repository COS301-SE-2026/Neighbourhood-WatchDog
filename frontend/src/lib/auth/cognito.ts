"use client";

import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
} from "amazon-cognito-identity-js";

const poolData = {
  UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
  ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
};

export const userPool = new CognitoUserPool(poolData);

export const signUp = (
  email: string,
  password: string,
  name: string,
  address: string
) => {
  const attributes = [
    new CognitoUserAttribute({
      Name: "name",
      Value: name,
    }),
    new CognitoUserAttribute({
      Name: "address",
      Value: address,
    }),
  ];

  return new Promise((resolve, reject) => {
    userPool.signUp(
      email,
      password,
      attributes,
      [],
      (err, result) => {
        if (err) {
          console.error(err);
          return reject(err);
        }

        resolve(result?.user);
      }
    );
  });
};

export const login = (email: string, password: string) => {
  const user = new CognitoUser({
    Username: email,
    Pool: userPool,
  });

  const authDetails = new AuthenticationDetails({
    Username: email,
    Password: password,
  });

  return new Promise<{ accessToken: string; idToken: string }>((resolve, reject) => {
    user.authenticateUser(authDetails, {
      onSuccess: (result) => {
        const accessToken = result.getAccessToken().getJwtToken();
        const idToken = result.getIdToken().getJwtToken();

        resolve({ accessToken, idToken });
      },

      onFailure: (err) => {
        console.error(err);
        reject(err);
      },
    });
  });
};

export const setSession = (tokens: { accessToken: string; idToken: string }) => {
  localStorage.setItem("accessToken", tokens.accessToken);
  localStorage.setItem("idToken", tokens.idToken);
};

export const getAccessToken = () => {
  return localStorage.getItem("accessToken");
};

export const isAuthenticated = () => {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("accessToken");
};

export const logout = () => {
  localStorage.clear();
};