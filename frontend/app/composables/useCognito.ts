import { CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserAttribute } from "amazon-cognito-identity-js";

export const useCognito = () => {
  const config = useRuntimeConfig();

  const poolData = {
    UserPoolId: config.public.cognitoUserPoolId as string,
    ClientId: config.public.cognitoClientId as string,
  };

  const userPool = new CognitoUserPool(poolData);

  // Register with Name and Email
  const registerUser = (email: string, password: string, name: string): Promise<any> => {
    return new Promise((resolve, reject) => {
      const attributeList = [new CognitoUserAttribute({ Name: "email", Value: email }), new CognitoUserAttribute({ Name: "name", Value: name })];

      // Generate a random internal username. Cognito will still allow login via the email alias.
      const internalUsername = "user_" + Math.random().toString(36).substring(2, 15);

      userPool.signUp(internalUsername, password, attributeList, [], (err, result) => {
        if (err) {
          reject(err.message || JSON.stringify(err));
          return;
        }
        resolve(result?.user);
      });
    });
  };

  // Change the first parameter from 'email' to 'username'
  const verifyEmail = (username: string, code: string): Promise<string> => {
    return new Promise((resolve, reject) => {
      // Use the internal username to verify the account
      const userData = { Username: username, Pool: userPool };
      const cognitoUser = new CognitoUser(userData);

      cognitoUser.confirmRegistration(code, true, (err, result) => {
        if (err) {
          reject(err.message || JSON.stringify(err));
          return;
        }
        resolve(result);
      });
    });
  };

  const loginUser = (email: string, password: string): Promise<string> => {
    return new Promise((resolve, reject) => {
      const authDetails = new AuthenticationDetails({ Username: email, Password: password });
      const userData = { Username: email, Pool: userPool };
      const cognitoUser = new CognitoUser(userData);

      cognitoUser.authenticateUser(authDetails, {
        onSuccess: (result) => {
          const accessToken = result.getIdToken().getJwtToken();
          resolve(accessToken);
        },
        onFailure: (err) => {
          reject(err.message || JSON.stringify(err));
        },
      });
    });
  };

  // 4. Request a password reset OTP
  const resetPassword = (email: string): Promise<any> => {
    return new Promise((resolve, reject) => {
      const userData = { Username: email, Pool: userPool };
      const cognitoUser = new CognitoUser(userData);

      cognitoUser.forgotPassword({
        onSuccess: (data) => resolve(data),
        onFailure: (err) => reject(err.message || JSON.stringify(err)),
      });
    });
  };

  // 5. Confirm the new password using the OTP
  const confirmPasswordReset = (email: string, code: string, newPassword: string): Promise<any> => {
    return new Promise((resolve, reject) => {
      const userData = { Username: email, Pool: userPool };
      const cognitoUser = new CognitoUser(userData);

      cognitoUser.confirmPassword(code, newPassword, {
        onSuccess: () => resolve("Password successfully reset"),
        onFailure: (err) => reject(err.message || JSON.stringify(err)),
      });
    });
  };

  return {
    registerUser,
    verifyEmail,
    loginUser,
    resetPassword, // NEW
    confirmPasswordReset, // NEW
  };
};
