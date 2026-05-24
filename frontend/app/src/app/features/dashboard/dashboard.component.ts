import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe, NgClass } from '@angular/common';
import { StatsService } from '../../services/stats.service';
import { ArtistsService } from '../../services/artists.service';
import {
  StatsSummary, TopTrack, TopArtista,
  DistribucionEnergia, LoadRecord,
} from '../../shared/models/api.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, DecimalPipe, NgClass],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
})
export class DashboardComponent implements OnInit {
  isLoading   = signal(true);
  hasError    = signal(false);
  summary     = signal<StatsSummary | null>(null);
  topTracks   = signal<TopTrack[]>([]);
  topArtists  = signal<TopArtista[]>([]);
  energyDist  = signal<DistribucionEnergia[]>([]);
  loadHistory = signal<LoadRecord[]>([]);
  maxEnergy   = computed(() => Math.max(...this.energyDist().map(e => e.cantidad_tracks ?? 0), 1));

  constructor(private stats: StatsService, private artistsSvc: ArtistsService) {}

  ngOnInit() { this.loadAll(); }

  loadAll() {
    this.isLoading.set(true);
    this.hasError.set(false);
    let loaded = 0;
    const done = () => { if (++loaded >= 4) this.isLoading.set(false); };
    const fail = () => { this.hasError.set(true); done(); };

    this.stats.getSummary().subscribe({ next: d => { this.summary.set(d); done(); }, error: fail });
    this.stats.getTopTracks(10).subscribe({ next: d => { this.topTracks.set(d); done(); }, error: () => done() });
    this.stats.getEnergyDistribution().subscribe({ next: d => { this.energyDist.set(d); done(); }, error: () => done() });
    this.stats.getLastLoads(5).subscribe({ next: d => { this.loadHistory.set(d); done(); }, error: () => done() });
    this.artistsSvc.getTopArtists(8).subscribe({ next: d => { this.topArtists.set(d); }, error: () => {} });
  }

  energyBar(count: number): number { return Math.round((count / this.maxEnergy()) * 100); }
  formatDate(d?: string): string {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('es', { day: '2-digit', month: 'short', year: '2-digit' }); }
    catch { return d; }
  }
  statusClass(s?: string): Record<string, boolean> {
    return { 'status-ok': s === 'ok' || s === 'success', 'status-warn': s === 'warn', 'status-error': s === 'error' };
  }
}
