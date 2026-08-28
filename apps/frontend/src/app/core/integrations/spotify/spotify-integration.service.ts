import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CatalogCacheService } from '../../services/catalog-cache.service';

export type SpotifyConnectionStatus =
  | 'not_configured'
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error';

export interface SpotifyProfile {
  id: string;
  display_name?: string | null;
  email?: string | null;
  country?: string;
  product?: string;
  images?: { url: string }[];
}

interface SpotifyTokenResponse {
  access_token: string;
  token_type: string;
  scope: string;
  expires_in: number;
  refresh_token?: string;
}

interface StoredSpotifySession extends SpotifyTokenResponse {
  expires_at: number;
}

interface SpotifyTrackPage {
  items: { id?: string | null; track?: { id?: string | null } }[];
}

export interface SpotifyTasteMixTrack {
  id_track: number;
  id_artista?: number;
  nombre_track?: string;
  nombre_artista?: string;
  score?: number;
  reason?: string;
  popularity?: number;
  spotify_track_id?: string | null;
  spotify_uri?: string | null;
  spotify_similarity?: number;
  source: 'spotify_taste_vox';
}

export interface SpotifyTasteMix {
  user_id: number;
  source: 'spotify_taste_vox';
  coverage: {
    spotify_signals: number;
    matched_catalog_tracks: number;
    match_percent: number;
  };
  tracks: SpotifyTasteMixTrack[];
}

export interface SpotifyExternalArtist {
  id: string;
  name: string;
  imageUrl?: string;
  source: 'spotify';
}

export interface SpotifyExternalTrack {
  id: string;
  name: string;
  artistName: string;
  albumName?: string;
  imageUrl?: string;
  durationMs?: number;
  popularity?: number;
  uri: string;
  source: 'spotify';
}

const SESSION_KEY = 'vox:spotify:session';
const VERIFIER_KEY = 'vox:spotify:pkce-verifier';
const STATE_KEY = 'vox:spotify:oauth-state';
const SPOTIFY_ACCOUNTS = 'https://accounts.spotify.com';
const SPOTIFY_API = 'https://api.spotify.com/v1';

@Injectable({ providedIn: 'root' })
export class SpotifyIntegrationService {
  private readonly http = inject(HttpClient);
  private readonly catalogCache = inject(CatalogCacheService);
  private session: StoredSpotifySession | null = this.readSession();

  readonly clientId = signal((environment.spotifyClientId ?? '').trim());
  readonly status = signal<SpotifyConnectionStatus>(
    this.clientId() ? (this.session ? 'connected' : 'disconnected') : 'not_configured',
  );
  readonly profile = signal<SpotifyProfile | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly configured = computed(() => !!this.clientId().trim());
  readonly connected = computed(() => this.status() === 'connected' && !!this.session);
  readonly redirectUri = `${window.location.origin}/integrations/spotify/callback`;

  async initializeFromCurrentUrl(): Promise<boolean> {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const oauthError = params.get('error');
    if (oauthError) {
      this.status.set('error');
      this.errorMessage.set('Spotify no autorizó la conexión. Puedes intentarlo otra vez.');
      this.clearOAuthQuery();
      return true;
    }
    if (code && state) {
      await this.finishAuthorization(code, state);
      this.clearOAuthQuery();
      return true;
    }
    if (this.session) {
      try {
        await this.loadProfile();
      } catch {
        // A stale session must not break the rest of settings.
      }
    }
    return false;
  }

  async connect(): Promise<void> {
    const clientId = this.clientId().trim();
    if (!clientId) throw new Error('Spotify no está configurado en esta instalación.');
    this.status.set('connecting');
    this.errorMessage.set(null);
    const verifier = randomBase64Url(64);
    const state = randomBase64Url(24);
    const challenge = await sha256Base64Url(verifier);
    sessionStorage.setItem(VERIFIER_KEY, verifier);
    sessionStorage.setItem(STATE_KEY, state);

    const scopes = [
      'streaming',
      'user-read-email',
      'user-read-private',
      'user-top-read',
      'user-read-recently-played',
      'user-library-read',
      'user-library-modify',
      'user-read-playback-state',
      'user-modify-playback-state',
    ];
    const query = new URLSearchParams({
      client_id: clientId,
      response_type: 'code',
      redirect_uri: this.redirectUri,
      code_challenge_method: 'S256',
      code_challenge: challenge,
      state,
      scope: scopes.join(' '),
      show_dialog: 'true',
    });
    window.location.assign(`${SPOTIFY_ACCOUNTS}/authorize?${query.toString()}`);
  }

  disconnect(): void {
    this.session = null;
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem(VERIFIER_KEY);
    sessionStorage.removeItem(STATE_KEY);
    this.profile.set(null);
    this.errorMessage.set(null);
    this.status.set(this.configured() ? 'disconnected' : 'not_configured');
  }

  async getAccessToken(): Promise<string> {
    if (!this.session) throw new Error('Conecta Spotify para continuar.');
    if (Date.now() >= this.session.expires_at - 60_000) await this.refresh();
    if (!this.session?.access_token) throw new Error('La sesión de Spotify venció.');
    return this.session.access_token;
  }

  async buildTasteMix(limit = 20): Promise<SpotifyTasteMix> {
    const token = await this.getAccessToken();
    const headers = { Authorization: `Bearer ${token}` };
    const [top, recent, saved] = await Promise.all([
      this.spotifyGet<SpotifyTrackPage>('/me/top/tracks?limit=30&time_range=medium_term', headers),
      this.spotifyGet<SpotifyTrackPage>('/me/player/recently-played?limit=30', headers),
      this.spotifyGet<SpotifyTrackPage>('/me/tracks?limit=30', headers),
    ]);
    const topIds = top.items.map((item) => ('id' in item ? item.id : item.track?.id)).filter(isTrackId);
    const recentIds = recent.items.map((item) => ('track' in item ? item.track?.id : item.id)).filter(isTrackId);
    const savedIds = saved.items.map((item) => ('track' in item ? item.track?.id : item.id)).filter(isTrackId);

    return firstValueFrom(
      this.http.post<SpotifyTasteMix>(`${environment.apiUrl}/smart/spotify-taste`, {
        top_track_ids: topIds,
        recent_track_ids: recentIds,
        saved_track_ids: savedIds,
        limit,
      }),
    );
  }

  /** Search Spotify's artist catalog when a user has connected an account. */
  async searchArtists(query: string, limit = 6): Promise<SpotifyExternalArtist[]> {
    if (!this.connected() || !query.trim()) return [];
    const token = await this.getAccessToken();
    const params = new URLSearchParams({ q: query.trim(), type: 'artist', limit: String(limit) });
    const result = await this.spotifyGet<{ artists?: { items?: Array<{ id?: string; name?: string; images?: Array<{ url?: string }> }> } }>(
      `/search?${params.toString()}`,
      { Authorization: `Bearer ${token}` },
    );
    return (result.artists?.items ?? [])
      .filter((artist): artist is { id: string; name: string; images?: Array<{ url?: string }> } => !!artist.id && !!artist.name)
      .map((artist) => ({
        id: artist.id,
        name: artist.name,
        imageUrl: artist.images?.[0]?.url,
        source: 'spotify' as const,
      }));
  }

  /** Live Spotify catalog search for connected sessions. The local warehouse
   * remains the offline catalog; this method only enriches a connected session. */
  async searchTracks(query: string, limit = 20): Promise<SpotifyExternalTrack[]> {
    const normalized = query.trim();
    if (!this.connected() || !normalized) return [];
    const safeLimit = Math.max(1, Math.min(limit, 50));
    const key = `spotify-track-search:${normalized.toLowerCase()}:${safeLimit}`;
    const cached = this.catalogCache.get<SpotifyExternalTrack[]>(key, 60_000);
    if (cached) return cached;
    const token = await this.getAccessToken();
    const params = new URLSearchParams({ q: normalized, type: 'track', limit: String(safeLimit) });
    const result = await this.spotifyGet<{
      tracks?: {
        items?: Array<{
          id?: string;
          name?: string;
          duration_ms?: number;
          popularity?: number;
          uri?: string;
          artists?: Array<{ name?: string }>;
          album?: { name?: string; images?: Array<{ url?: string }> };
        }>;
      };
    }>(`/search?${params.toString()}`, { Authorization: `Bearer ${token}` });
    const tracks = (result.tracks?.items ?? [])
      .filter((track): track is {
        id: string;
        name: string;
        duration_ms?: number;
        popularity?: number;
        uri?: string;
        artists?: Array<{ name?: string }>;
        album?: { name?: string; images?: Array<{ url?: string }> };
      } => !!track.id && !!track.name)
      .map((track) => ({
        id: track.id,
        name: track.name,
        artistName: track.artists?.map((artist) => artist.name).filter(Boolean).join('; ') || 'Artista desconocido',
        albumName: track.album?.name,
        imageUrl: track.album?.images?.[0]?.url,
        durationMs: track.duration_ms,
        popularity: track.popularity,
        uri: track.uri || `spotify:track:${track.id}`,
        source: 'spotify' as const,
      }));
    this.catalogCache.set(key, tracks, 60_000);
    return tracks;
  }

  private async finishAuthorization(code: string, state: string): Promise<void> {
    const expectedState = sessionStorage.getItem(STATE_KEY);
    const verifier = sessionStorage.getItem(VERIFIER_KEY);
    if (!expectedState || expectedState !== state || !verifier) {
      this.status.set('error');
      this.errorMessage.set('La respuesta de Spotify no coincide con esta sesión. Vuelve a conectar.');
      return;
    }
    this.status.set('connecting');
    const body = new URLSearchParams({
      client_id: this.clientId(),
      grant_type: 'authorization_code',
      code,
      redirect_uri: this.redirectUri,
      code_verifier: verifier,
    });
    const response = await fetch(`${SPOTIFY_ACCOUNTS}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!response.ok) {
      this.status.set('error');
      this.errorMessage.set('No pudimos completar la conexión con Spotify. Revisa el Client ID y la URL de retorno.');
      return;
    }
    this.storeSession((await response.json()) as SpotifyTokenResponse);
    sessionStorage.removeItem(VERIFIER_KEY);
    sessionStorage.removeItem(STATE_KEY);
    await this.loadProfile();
  }

  private async refresh(): Promise<void> {
    if (!this.session?.refresh_token) {
      this.disconnect();
      throw new Error('Vuelve a conectar Spotify para renovar la sesión.');
    }
    const body = new URLSearchParams({
      client_id: this.clientId(),
      grant_type: 'refresh_token',
      refresh_token: this.session.refresh_token,
    });
    const response = await fetch(`${SPOTIFY_ACCOUNTS}/api/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!response.ok) {
      this.disconnect();
      throw new Error('Spotify pidió volver a iniciar sesión.');
    }
    this.storeSession((await response.json()) as SpotifyTokenResponse, this.session.refresh_token);
  }

  private async loadProfile(): Promise<void> {
    const token = await this.getAccessToken();
    const profile = await this.spotifyGet<SpotifyProfile>('/me', {
      Authorization: `Bearer ${token}`,
    });
    this.profile.set(profile);
    this.status.set('connected');
    this.errorMessage.set(null);
  }

  private async spotifyGet<T>(path: string, headers: Record<string, string>): Promise<T> {
    const response = await fetch(`${SPOTIFY_API}${path}`, { headers });
    if (!response.ok) throw new Error(`Spotify API ${response.status}`);
    return response.json() as Promise<T>;
  }

  private storeSession(token: SpotifyTokenResponse, existingRefresh?: string): void {
    this.session = {
      ...token,
      refresh_token: token.refresh_token ?? existingRefresh,
      expires_at: Date.now() + token.expires_in * 1000,
    };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(this.session));
    this.status.set('connected');
  }

  private readSession(): StoredSpotifySession | null {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      return raw ? (JSON.parse(raw) as StoredSpotifySession) : null;
    } catch {
      return null;
    }
  }

  private clearOAuthQuery(): void {
    const url = new URL(window.location.href);
    ['code', 'state', 'error'].forEach((key) => url.searchParams.delete(key));
    window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
  }
}

function isTrackId(value: string | null | undefined): value is string {
  return typeof value === 'string' && value.length > 0;
}

function randomBase64Url(size: number): string {
  const bytes = new Uint8Array(size);
  crypto.getRandomValues(bytes);
  return base64Url(bytes);
}

async function sha256Base64Url(value: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return base64Url(new Uint8Array(digest));
}

function base64Url(bytes: Uint8Array): string {
  let binary = '';
  bytes.forEach((byte) => (binary += String.fromCharCode(byte)));
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}
