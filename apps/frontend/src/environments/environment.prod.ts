export const environment = {
  production: true,
  // URL relativa: nginx hace proxy /api/v1 → backend (ver frontend/nginx.conf)
  apiUrl: '/api/v1',
  // Public OAuth identifier installed once for the whole application.
  spotifyClientId: '5669baab13d1497f9b07e4b740fed691',
  devVerificationChannel: false,
};
