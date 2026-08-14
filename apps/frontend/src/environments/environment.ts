export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  /**
   * Shows the verification/reset code returned by the local backend so sign-up and
   * recovery can be exercised without a mail server. Must stay false in production.
   */
  devVerificationChannel: true,
};
