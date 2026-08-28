export const environment = {
  production: false,
  // Same-origin in development; the Angular proxy forwards /api to :8000.
  // This avoids localhost/127.0.0.1 CORS mismatches across browsers.
  apiUrl: '/api/v1',
  // Public OAuth identifier installed once for the whole application.
  spotifyClientId: '5669baab13d1497f9b07e4b740fed691',
  /**
   * Shows the verification/reset code returned by the local backend so sign-up and
   * recovery can be exercised without a mail server. Must stay false in production.
   */
  devVerificationChannel: true,
};
