import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { HomeHeroComponent } from './home-hero.component';
import { HomeAnalyticsBandComponent } from './home-analytics-band.component';
import { I18nService } from '../../../../core/services/i18n.service';
import { StatsService } from '../../../analytics/services/stats.service';
import { StatsSummary } from '../../../../shared/models/api.models';

const summary = {
  total_tracks: 1200,
  total_artistas: 340,
  total_generos: 40,
  total_albumes: 510,
  total_events: 90000,
  total_streams: 90000,
  total_playlists: 88,
  events_classification_totals: { synthetic: 90000 },
} as StatsSummary;

function i18nStub() {
  return {
    lang: () => 'es' as const,
    t: (k: string, params?: Record<string, unknown>) => {
      const map: Record<string, string> = {
        'home.greeting.afternoon': 'Buenas tardes',
        'home.title': 'Descubre',
        'home.subtitle': 'Subtítulo',
        'home.searchPlaceholder': 'Buscar',
        'home.discover.catalog': 'Catálogo',
        'home.discover.playlists': 'Playlists',
        'home.discover.genres': 'Géneros',
        'home.chip.today': `Hoy ${params?.['min'] ?? 0} min`,
        'home.chip.weeklyGoal': `Meta ${params?.['pct'] ?? 0}%`,
        'home.chip.explorer': `Nivel ${params?.['level'] ?? 1}`,
        'home.chip.streak': `Racha ${params?.['count'] ?? 0}`,
        'home.chip.streakOne': 'Racha 1',
        'home.catalogDemo.title': 'Catálogo global de demostración',
        'home.catalogDemo.subtitle': 'Indicadores del warehouse importado',
        'home.stat.events': 'Eventos',
        'home.stat.tracks': 'Tracks',
        'home.stat.artists': 'Artistas',
        'home.stat.albums': 'Álbumes',
        'home.stat.playlists': 'Playlists',
        'home.stat.eventsSubSynthetic': 'Sintéticos',
        'home.stat.tracksSub': 'Importados',
        'home.stat.artistsSub': 'Importados',
        'home.stat.albumsSub': 'Importados',
        'home.stat.playlistsSub': 'Importados',
        'home.rail.title': 'Panel analítico',
        'home.rail.viewMore': 'Ver más',
        'home.kpi.favorites': 'Favoritos',
        'home.kpi.favoritesSub': 'Tus guardados',
        'home.kpi.favoritesTip': 'Favoritos tip',
        'home.widget.catalogGrowth': 'Crecimiento',
        'home.widget.catalogGrowthCtx': 'ctx',
        'home.widget.byHour': 'Por hora',
        'home.widget.byHourCtx': 'ctx',
        'home.widget.byGenre': 'Por género',
        'home.widget.byGenreCtx': 'ctx',
        'home.widget.tracksUnit': 'tracks',
        'home.widget.topArtists': 'Top artistas',
        'home.widget.topArtistsCtx': 'ctx',
        'home.widget.topGenres': 'Top géneros',
        'home.widget.topGenresCtx': 'ctx',
        'home.widget.weeklyTime': 'Tiempo semanal',
        'home.widget.weeklyTimeCtx': 'ctx',
        'home.widget.weeklyTimeFoot': 'foot',
        'home.rail.chartEmpty': 'vacío',
        'home.widget.noListens': 'sin escuchas',
        'home.goal.title': 'Meta semanal',
        'home.goal.progress': 'progreso',
      };
      return map[k] ?? k;
    },
  };
}

describe('Home presentation consolidation', () => {
  describe('HomeHeroComponent', () => {
    let fixture: ComponentFixture<HomeHeroComponent>;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [HomeHeroComponent],
        providers: [
          provideRouter([]),
          { provide: I18nService, useValue: i18nStub() },
          {
            provide: StatsService,
            useValue: { getEventsBreakdown: () => of(null) },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(HomeHeroComponent);
      fixture.componentRef.setInput('greetingKey', 'home.greeting.afternoon');
      fixture.componentRef.setInput('userName', 'Alex');
      fixture.componentRef.setInput('userPlan', 'Free');
      fixture.componentRef.setInput('summary', summary);
      fixture.componentRef.setInput('listenMinutesToday', 12);
      fixture.componentRef.setInput('weeklyGoalPct', 40);
      fixture.componentRef.setInput('explorerLevel', 2);
      fixture.detectChanges();
    });

    it('keeps user-focus chips and omits global warehouse KPIs from the hero', () => {
      const root = fixture.nativeElement as HTMLElement;
      expect(root.querySelector('[data-testid="home-hero-user-focus"]')).toBeTruthy();
      expect(root.querySelector('.hero-stats')).toBeNull();
      expect(root.querySelector('[data-testid="home-catalog-demo"]')).toBeNull();

      const text = root.textContent || '';
      expect(text).toContain('Free');
      expect(text).toContain('Hoy 12 min');
      expect(text).toContain('Meta 40%');
      expect(text).toContain('Nivel 2');

      // Warehouse KPI labels must not appear in the personal hero.
      expect(text).not.toMatch(/\bEventos\b/);
      expect(text).not.toMatch(/\bTracks\b/);
      expect(text).not.toMatch(/\bArtistas\b/);
      expect(text).not.toMatch(/\bÁlbumes\b/);
    });
  });

  describe('HomeAnalyticsBandComponent', () => {
    let fixture: ComponentFixture<HomeAnalyticsBandComponent>;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [HomeAnalyticsBandComponent],
        providers: [
          provideRouter([]),
          { provide: I18nService, useValue: i18nStub() },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(HomeAnalyticsBandComponent);
      fixture.componentRef.setInput('summary', summary);
      fixture.componentRef.setInput('favoritesCount', 7);
      fixture.componentRef.setInput('growthValues', []);
      fixture.componentRef.setInput('hourlyBuckets', Array(24).fill(0));
      fixture.componentRef.setInput('genreBars', []);
      fixture.componentRef.setInput('artists', []);
      fixture.componentRef.setInput('genres', []);
      fixture.detectChanges();
    });

    it('renders global warehouse KPIs once in the labeled catalog demo strip', () => {
      const root = fixture.nativeElement as HTMLElement;
      const strips = root.querySelectorAll('[data-testid="home-catalog-demo"]');
      expect(strips.length).toBe(1);
      expect(strips[0].getAttribute('aria-label')).toContain('Catálogo global de demostración');
      expect(strips[0].textContent).toContain('Catálogo global de demostración');

      const stats = strips[0].querySelectorAll('.catalog-demo__stat');
      expect(stats.length).toBe(5);

      const labelText = Array.from(stats)
        .map((el) => (el.querySelector('span')?.textContent || '').trim())
        .join('|');
      expect(labelText).toContain('Eventos');
      expect(labelText).toContain('Tracks');
      expect(labelText).toContain('Artistas');
      expect(labelText).toContain('Álbumes');
      expect(labelText).toContain('Playlists');

      // Each warehouse label appears once in the catalog strip (and not again in personal KPIs).
      for (const label of ['Eventos', 'Tracks', 'Artistas', 'Álbumes']) {
        const inStrip = (
          (strips[0].textContent || '').match(new RegExp(label, 'g')) || []
        ).length;
        expect(inStrip).toBe(1);
      }

      const personal = root.querySelector('[data-testid="home-personal-kpi-strip"]');
      expect(personal).toBeTruthy();
      expect(personal!.textContent).toContain('Favoritos');
      expect(personal!.textContent).not.toContain('Eventos');
      expect(personal!.textContent).not.toContain('Tracks');
    });
  });
});
