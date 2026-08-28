import { Injectable, Injector, ProviderToken, inject } from '@angular/core';
import { SpotifyIntegrationService } from '../integrations/spotify/spotify-integration.service';
import { ArtistContextService } from '../../packages/artist-space/services/artist-context.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { HistoryService } from '../../packages/streaming/services/history.service';
import { MusicPlayerService } from '../../shared/services/music-player.service';
import { RETURN_URL_STORAGE_KEY } from './return-url';
import { SpaceContextService } from './space-context.service';
import { SPACE_STORAGE_KEY } from './space.models';

/** Kept in sync with ProfileSwitchService — “Who's listening?” must re-run per auth session. */
const PROFILE_SESSION_SELECTED_KEY = 'voxmetriks_profile_session_selected';

/**
 * Single place that wipes private client state on logout / 401 (Spec 050).
 *
 * Dependencies are resolved lazily through the Injector: AuthService injects this
 * coordinator, and SpaceContextService injects AuthService, so eager field
 * injection would form a construction-time cycle.
 */
@Injectable({ providedIn: 'root' })
export class SessionCleanupCoordinator {
  private readonly injector = inject(Injector);

  clearPrivateClientState(): void {
    this.run(() => this.resolve(MusicPlayerService)?.stopPlayback());
    this.run(() => this.resolve(SpotifyIntegrationService)?.disconnect());
    this.run(() => this.resolve(OrganizationContextService)?.clearOrganizationScopedState());
    this.run(() => this.resolve(ArtistContextService)?.clear());
    this.run(() => this.resolve(SpaceContextService)?.clear());
    // Local cache only — account history is server-side data and must survive logout.
    this.run(() => this.resolve(HistoryService)?.clearLocalCache?.());
    this.run(() => sessionStorage.removeItem(RETURN_URL_STORAGE_KEY));
    this.run(() => sessionStorage.removeItem(PROFILE_SESSION_SELECTED_KEY));
    this.run(() => localStorage.removeItem(SPACE_STORAGE_KEY));
  }

  private resolve<T>(token: ProviderToken<T>): T | null {
    try {
      return this.injector.get(token, null);
    } catch {
      return null;
    }
  }

  private run(step: () => void): void {
    try {
      step();
    } catch {
      /* cleanup is best-effort: one failing collaborator must not block the rest */
    }
  }
}
