declare module 'amazon-cognito-identity-js' {
  export interface ICognitoUserPoolData {
    UserPoolId: string
    ClientId: string
  }

  export interface IAuthenticationDetailsData {
    Username: string
    Password: string
  }

  export interface CognitoUserAttribute {
    getName(): string
    getValue(): string
  }

  export interface ISignUpResult {
    user: CognitoUser
    userSub: string
  }

  export interface CognitoUserAttributeData {
    Name: string
    Value: string
  }

  export interface AuthenticationCallbacks {
    onSuccess?: (session: CognitoUserSession) => void
    onFailure?: (error: Error) => void
    newPasswordRequired?: (userAttributes: Record<string, string>, requiredAttributes: string[]) => void
  }

  export class CognitoUserPool {
    constructor(data: ICognitoUserPoolData)
    getCurrentUser(): CognitoUser | null
    getCurrentUserSync(): CognitoUser | null
    signUp(username: string, password: string, userAttributes: CognitoUserAttributeData[], validationData: CognitoUserAttributeData[], callback: (err: Error | null, result?: ISignUpResult) => void): void
  }

  export class CognitoUser {
    getUsername(): string
    getAuthenticationFlowType(): string
    authenticateUser(authenticationDetails: AuthenticationDetails, callbacks: AuthenticationCallbacks): void
    getUserAttributes(callback: (err: Error | null, attributes?: CognitoUserAttribute[]) => void): void
    getSession(callback: (err: Error | null, session?: CognitoUserSession) => void): void
    signOut(): void
    changePassword(oldPassword: string, newPassword: string, callback: (err: Error | null) => void): void
    confirmRegistration(code: string, forceAliasCreation: boolean, callback: (err: Error | null, result?: string) => void): void
    completeNewPasswordChallenge(newPassword: string, userAttributes: Record<string, string>, callbacks: AuthenticationCallbacks): void
  }

  export class AuthenticationDetails {
    constructor(data: IAuthenticationDetailsData)
  }

  export interface CognitoUserSession {
    isValid(): boolean
    getAccessToken(): CognitoAccessToken
    getIdToken(): CognitoIdToken
    getRefreshToken(): CognitoRefreshToken
  }

  export interface CognitoAccessToken {
    getJwtToken(): string
  }

  export interface CognitoIdToken {
    getJwtToken(): string
  }

  export interface CognitoRefreshToken {
    getToken(): string
  }

  export class CognitoIdentityServiceProvider {
    constructor(config: Record<string, unknown>)
  }
}
