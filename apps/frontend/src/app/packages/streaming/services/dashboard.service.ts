import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReadCache } from '../../../core/http/read-cache';
import {
  StatsSummary, TopTrack, CatalogGrowthPoint, Track, GeneroPopularidad,
  PlaylistSummary, Artista, PaginatedResponse,
} from '../../../shared/models/api.models';

export interface HomeFeedPayload {
  summary: StatsSummary;
  top_tracks: TopTrack[];
  catalog_growth: CatalogGrowthPoint[];
  discover: PaginatedResponse<Track>;
  genres: GeneroPopularidad[];
  artists: Artista[];
  /** Popular warehouse playlists for the home rail. */
  playlists: PlaylistSummary[];
  /** User's personal playlist count (KPI band). */
  my_playlist_count?: number;
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/dashboard`;
  private readonly homeCache = new ReadCache<HomeFeedPayload>();

  getHomeFeed(discoverPage = 1): Observable<HomeFeedPayload> {
    const params = new HttpParams().set('discover_page', discoverPage);
    return this.homeCache.get(() =>
      this.http.get<HomeFeedPayload>(`${this.API}/home`, { params }),
    );
  }

  invalidateHomeFeed(): void {
    this.homeCache.invalidate();
  }
}
