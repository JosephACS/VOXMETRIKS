import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../shared/services/icon-render.service';
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KpiCardComponent } from '../../shared/components/kpi-card/kpi-card.component';
import { MetricBarComponent } from '../../shared/components/metric-bar/metric-bar.component';

interface ForYouTrack {
  id: number;
  track: string;
  artist: string;
  score: number;
  tags: string[];
  accent: string;
}

interface RecommendedArtist {
  id: number;
  name: string;
  genre: string;
  popularity: number;
  affinity: number;
  gradient: string;
  initial: string;
}

interface MoodCard {
  id: string;
  name: string;
  description: string;
  tracks: number;
  gradient: string;
  iconKey: string;
}

interface TrendingRow {
  id: number;
  song: string;
  genre: string;
  popularity: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
}

interface GenreAffinity {
  genre: string;
  score: number;
  color: string;
}

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, KpiCardComponent, MetricBarComponent],
  templateUrl: './recommendations.component.html',
  styleUrls: ['./recommendations.component.css'],
})
export class RecommendationsComponent {
  private iconRender = inject(IconRenderService);

  selectedMood = signal<string | null>(null);

  forYouTracks: ForYouTrack[] = [
    { id: 1, track: 'Midnight City', artist: 'M83', score: 96, tags: ['Synth-pop', 'Energético', 'Nostálgico'], accent: '#7c3aed' },
    { id: 2, track: 'Electric Feel', artist: 'MGMT', score: 94, tags: ['Indie', 'Psichedélico', 'Dance'], accent: '#1ed896' },
    { id: 3, track: 'Redbone', artist: 'Childish Gambino', score: 92, tags: ['R&B', 'Soul', 'Chill'], accent: '#10b981' },
    { id: 4, track: 'Titanium', artist: 'David Guetta ft. Sia', score: 91, tags: ['EDM', 'Pop', 'Workout'], accent: '#3b82f6' },
    { id: 5, track: 'Starboy', artist: 'The Weeknd', score: 89, tags: ['R&B', 'Dark Pop', 'Nocturno'], accent: '#ec4899' },
    { id: 6, track: 'Blinding Lights', artist: 'The Weeknd', score: 88, tags: ['Synthwave', '80s', 'Pop'], accent: '#f59e0b' },
  ];

  recommendedArtists: RecommendedArtist[] = [
    { id: 1, name: 'Dua Lipa', genre: 'Pop / Dance', popularity: 89, affinity: 94, gradient: 'linear-gradient(135deg, #1ed896, #ec4899)', initial: 'DL' },
    { id: 2, name: 'The Weeknd', genre: 'R&B / Pop', popularity: 92, affinity: 91, gradient: 'linear-gradient(135deg, #7c3aed, #1e1b4b)', initial: 'TW' },
    { id: 3, name: 'Billie Eilish', genre: 'Alternative', popularity: 87, affinity: 88, gradient: 'linear-gradient(135deg, #10b981, #064e3b)', initial: 'BE' },
    { id: 4, name: 'Calvin Harris', genre: 'EDM', popularity: 85, affinity: 86, gradient: 'linear-gradient(135deg, #3b82f6, #1e3a8a)', initial: 'CH' },
    { id: 5, name: 'Bad Bunny', genre: 'Reggaetón', popularity: 90, affinity: 82, gradient: 'linear-gradient(135deg, #f59e0b, #b45309)', initial: 'BB' },
    { id: 6, name: 'Arctic Monkeys', genre: 'Indie Rock', popularity: 83, affinity: 79, gradient: 'linear-gradient(135deg, #6366f1, #312e81)', initial: 'AM' },
  ];

  moodCards: MoodCard[] = [
    { id: 'chill', name: 'Chill', description: 'Relajado y atmosférico', tracks: 48, gradient: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)', iconKey: 'moon' },
    { id: 'workout', name: 'Workout', description: 'Alta energía para entrenar', tracks: 62, gradient: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)', iconKey: 'dumbbell' },
    { id: 'focus', name: 'Focus', description: 'Concentración y productividad', tracks: 35, gradient: 'linear-gradient(135deg, #10b981 0%, #047857 100%)', iconKey: 'target' },
    { id: 'party', name: 'Party', description: 'Fiesta y buen ambiente', tracks: 55, gradient: 'linear-gradient(135deg, #1ed896 0%, #148f5e 100%)', iconKey: 'party' },
    { id: 'relax', name: 'Relax', description: 'Calma y bienestar', tracks: 41, gradient: 'linear-gradient(135deg, #a78bfa 0%, #6d28d9 100%)', iconKey: 'leaf' },
  ];

  trendingRows: TrendingRow[] = [
    { id: 1, song: 'Flowers', genre: 'Pop', popularity: 91, trend: 'up', change: 12 },
    { id: 2, song: 'As It Was', genre: 'Pop / Indie', popularity: 88, trend: 'up', change: 8 },
    { id: 3, song: 'Unholy', genre: 'Pop / R&B', popularity: 85, trend: 'stable', change: 0 },
    { id: 4, song: 'Heat Waves', genre: 'Indie Pop', popularity: 84, trend: 'down', change: -3 },
    { id: 5, song: 'Stay', genre: 'Pop / EDM', popularity: 82, trend: 'up', change: 5 },
    { id: 6, song: 'Shivers', genre: 'Pop', popularity: 80, trend: 'down', change: -2 },
    { id: 7, song: 'Peaches', genre: 'R&B / Pop', popularity: 78, trend: 'stable', change: 0 },
    { id: 8, song: 'Levitating', genre: 'Dance Pop', popularity: 86, trend: 'up', change: 6 },
  ];

  genreAffinities: GenreAffinity[] = [
    { genre: 'Pop', score: 92, color: '#1ed896' },
    { genre: 'R&B', score: 85, color: '#7c3aed' },
    { genre: 'Indie', score: 78, color: '#10b981' },
    { genre: 'EDM', score: 74, color: '#3b82f6' },
    { genre: 'Rock', score: 68, color: '#ef4444' },
    { genre: 'Latin', score: 65, color: '#f59e0b' },
    { genre: 'Hip-Hop', score: 61, color: '#ec4899' },
  ];

  maxGenreScore = Math.max(...this.genreAffinities.map((g) => g.score));

  chartPoints = [
    { x: 80, y: 95 }, { x: 120, y: 110 }, { x: 160, y: 70 },
    { x: 200, y: 85 }, { x: 240, y: 55 }, { x: 280, y: 75 }, { x: 300, y: 60 },
  ];

  selectMood(id: string) {
    this.selectedMood.update((current) => (current === id ? null : id));
  }

  trendIcon(trend: TrendingRow['trend']): string {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  }

  trendClass(trend: TrendingRow['trend']): string {
    if (trend === 'up') return 'trend-up';
    if (trend === 'down') return 'trend-down';
    return 'trend-stable';
  }

  genreBarWidth(score: number): number {
    return Math.round((score / this.maxGenreScore) * 100);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
