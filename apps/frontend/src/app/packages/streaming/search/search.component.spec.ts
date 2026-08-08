import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { SearchComponent } from './search.component';
import { TracksService } from '../services/tracks.service';
import { ArtistsService } from '../services/artists.service';
import { SearchHistoryService } from '../services/search-history.service';
import { AIService } from '../../ai/services/ai.service';
import { PlayerController } from '../../../playback-core/player.controller';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { environment } from '../../../../environments/environment';

describe('TracksService music-search contracts', () => {
  let svc: TracksService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), TracksService],
    });
    svc = TestBed.inject(TracksService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('musicSearch hits /tracks/music-search with allow_external', () => {
    svc.musicSearch('query', 1, 20, false).subscribe();
    const req = http.expectOne(
      (r) => r.url === `${environment.apiUrl}/tracks/music-search`,
    );
    expect(req.request.params.get('q')).toBe('query');
    expect(req.request.params.get('allow_external')).toBe('false');
    req.flush({
      query: 'query',
      phase: 'local_empty',
      message: '',
      local: { items: [], total: 0, page: 1, limit: 20 },
      external: [],
      external_available: true,
    });
  });

  it('adoptYoutubeResult posts require_preferred when requested', () => {
    svc.adoptYoutubeResult('vid', 7, { requirePreferred: true }).subscribe();
    const first = http.expectOne(`${environment.apiUrl}/tracks/music-search/adopt`);
    expect(first.request.body).toEqual({
      video_id: 'vid',
      track_id: 7,
      require_preferred: true,
    });
    first.flush({ track_id: 1, created: true, video_id: 'vid' });

    svc.adoptYoutubeResult('vid').subscribe();
    const second = http.expectOne(`${environment.apiUrl}/tracks/music-search/adopt`);
    expect(second.request.body).toEqual({ video_id: 'vid' });
    second.flush({ track_id: 2, created: true, video_id: 'vid' });
  });
});

describe('SearchComponent music-core flows', () => {
  let fixture: ComponentFixture<SearchComponent>;
  let component: SearchComponent;
  let musicSearch: ReturnType<typeof vi.fn>;
  let adoptYoutubeResult: ReturnType<typeof vi.fn>;
  let playTrack: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    musicSearch = vi.fn();
    adoptYoutubeResult = vi.fn();
    playTrack = vi.fn();

    TestBed.overrideComponent(SearchComponent, {
      set: {
        imports: [CommonModule, FormsModule],
        template: `
          <p data-testid="phase">{{ phase() }}</p>
          <p data-testid="error">{{ errorMessage() }}</p>
        `,
        styles: [],
        templateUrl: undefined as unknown as string,
        styleUrls: [],
      },
    });

    await TestBed.configureTestingModule({
      // Do not import SearchComponent in imports[] — avoids nested templateUrl walk under Vitest JIT.
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { queryParamMap: of(convertToParamMap({})) },
        },
        { provide: TracksService, useValue: { musicSearch, adoptYoutubeResult } },
        {
          provide: ArtistsService,
          useValue: {
            listArtists: vi.fn(() => of({ items: [], total: 0, page: 1, limit: 20 })),
          },
        },
        {
          provide: SearchHistoryService,
          useValue: { add: vi.fn(), history$: of([]), reload: vi.fn() },
        },
        { provide: AIService, useValue: { naturalSearch: vi.fn() } },
        { provide: PlayerController, useValue: { playTrack } },
        { provide: CoverArtService, useValue: { gradientFor: () => 'g' } },
        { provide: IconRenderService, useValue: { render: () => '' } },
        {
          provide: I18nService,
          useValue: { lang: signal('es'), t: (k: string) => k },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('falls back local → YouTube when local total is 0', async () => {
    vi.useFakeTimers();
    musicSearch
      .mockImplementationOnce((_q: string, _p: number, _l: number, allowExternal: boolean) => {
        expect(allowExternal).toBe(false);
        return of({
          query: 'rare song',
          phase: 'local_empty',
          message: '',
          local: { items: [], total: 0, page: 1, limit: 20 },
          external: [],
          missing_local: [],
          external_available: true,
        });
      })
      .mockImplementationOnce((_q: string, _p: number, _l: number, allowExternal: boolean) => {
        expect(allowExternal).toBe(true);
        return of({
          query: 'rare song',
          phase: 'external',
          message: 'Buscando en YouTube…',
          local: { items: [], total: 0, page: 1, limit: 20 },
          external: [{ video_id: 'yt1', title: 'Rare Song' }],
          missing_local: [],
          external_available: true,
        });
      });

    component.runSearch('rare song', false);
    await vi.advanceTimersByTimeAsync(400); // first local pass
    await vi.advanceTimersByTimeAsync(400); // auto YouTube fallback debounce
    fixture.detectChanges();

    expect(musicSearch).toHaveBeenCalledTimes(2);
    expect(component.externalResults()).toHaveLength(1);
    expect(component.phase()).toBe('external');
    vi.useRealTimers();
  });

  it('compatible adopt sends requirePreferred when exactly one missing local', () => {
    component.missingLocal.set([{ id_track: 42, nombre_track: 'Local Hit' }]);
    adoptYoutubeResult.mockReturnValue(
      of({
        track_id: 42,
        created: false,
        video_id: 'vid',
        title: 'Local Hit',
        channel_title: 'Artist',
      }),
    );

    component.playExternal({ video_id: 'vid', title: 'Local Hit', channel_title: 'Artist' });

    expect(adoptYoutubeResult).toHaveBeenCalledWith('vid', 42, { requirePreferred: true });
    expect(playTrack).toHaveBeenCalled();
    expect(component.hasError()).toBe(false);
  });

  it('retries adopt once without track_id after 409 TRACK_SOURCE_MISMATCH', () => {
    component.missingLocal.set([{ id_track: 7, nombre_track: 'Mismatch' }]);
    adoptYoutubeResult
      .mockReturnValueOnce(
        throwError(() => ({
          status: 409,
          error: { detail: { code: 'TRACK_SOURCE_MISMATCH' } },
        })),
      )
      .mockReturnValueOnce(
        of({
          track_id: 100,
          created: true,
          video_id: 'vid',
          title: 'Independent',
        }),
      );

    component.playExternal({ video_id: 'vid', title: 'Independent' });

    expect(adoptYoutubeResult).toHaveBeenNthCalledWith(1, 'vid', 7, { requirePreferred: true });
    expect(adoptYoutubeResult).toHaveBeenNthCalledWith(2, 'vid');
    expect(component.trackResults().some((r) => r.id_track === 100)).toBe(true);
    expect(component.hasError()).toBe(false);
  });

  it('surfaces final error when adopt and 409-retry both fail', () => {
    component.missingLocal.set([{ id_track: 7, nombre_track: 'Bad' }]);
    adoptYoutubeResult
      .mockReturnValueOnce(
        throwError(() => ({
          status: 409,
          error: { detail: { code: 'TRACK_SOURCE_MISMATCH' } },
        })),
      )
      .mockReturnValueOnce(throwError(() => ({ status: 500, error: { detail: 'boom' } })));

    component.playExternal({ video_id: 'vid', title: 'Fail' });

    expect(adoptYoutubeResult).toHaveBeenCalledTimes(2);
    expect(component.hasError()).toBe(true);
    expect(component.errorMessage()).toContain('No fue posible preparar la canción');
    expect(component.phase()).toBe('external_error');
  });

  it('preserves AI naturalSearch mode alongside musicSearch', () => {
    expect(component.aiMode()).toBe(false);
    const ai = TestBed.inject(AIService) as unknown as { naturalSearch: ReturnType<typeof vi.fn> };
    expect(ai.naturalSearch).toBeDefined();
    expect(typeof musicSearch).toBe('function');
  });
});
