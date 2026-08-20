import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { StatsService } from '../../analytics/services/stats.service';
import { LoadRecord, StatsSummary, SyntheticLimits } from '../../../shared/models/api.models';
import { I18nService } from '../../../core/services/i18n.service';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

type LayerStatus = 'ready' | 'idle' | 'running' | 'success' | 'warning' | 'failed';
type PipelineState = 'idle' | 'running' | 'completed' | 'failed';
type LogLevel = 'INFO' | 'WARN' | 'SUCCESS';
type OverallStateKey = 'idle' | 'running' | 'completed' | 'failed' | 'offline';

interface TimelineStep {
  id: string;
  name: string;
  status: LayerStatus;
  records: number;
  durationMs: number | null;
  error: string | null;
}

interface LogEntry {
  time: string;
  level: LogLevel;
  message: string;
}

interface PipelineIncident {
  stage: string;
  message: string;
  time: string;
}

interface MultiplierPreset {
  key: 1 | 2 | 3 | 4;
  label: string;
}

type VolumeMode = 'multiplier' | 'custom';

@Component({
  selector: 'app-elt-pipeline',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  templateUrl: './elt-pipeline.component.html',
  styleUrls: ['./elt-pipeline.component.css'],
})
export class EltPipelineComponent implements OnInit, OnDestroy {
  readonly lang = inject(I18nService).lang;
  private i18n = inject(I18nService);
  private confirm = inject(ConfirmDialogService);
  private stats = inject(StatsService);

  private runTimer: ReturnType<typeof setInterval> | null = null;
  private elapsedTimer: ReturnType<typeof setInterval> | null = null;
  private runStartMs = 0;

  isLoadingKpis = signal(true);
  apiConnected = signal(false);
  summary = signal<StatsSummary | null>(null);
  lastLoad = signal<LoadRecord | null>(null);
  limits = signal<SyntheticLimits | null>(null);

  pipelineState = signal<PipelineState>('idle');
  runProgress = signal(0);
  volumeMode = signal<VolumeMode>('multiplier');
  selectedMultiplier = signal<1 | 2 | 3 | 4>(2);
  customTarget = signal(400_000);
  logs = signal<LogEntry[]>([]);
  lastError = signal<PipelineIncident | null>(null);
  lastRunDurationSec = signal<number | null>(null);
  elapsedSeconds = signal(0);
  warehouseSizeMb = signal(0);

  timeline = signal<TimelineStep[]>([
    { id: 'extract', name: 'Extracción', status: 'ready', records: 0, durationMs: null, error: null },
    { id: 'bronze', name: 'Carga', status: 'ready', records: 0, durationMs: null, error: null },
    { id: 'silver', name: 'Transformación', status: 'ready', records: 0, durationMs: null, error: null },
    { id: 'gold', name: 'Modelado', status: 'ready', records: 0, durationMs: null, error: null },
    { id: 'warehouse', name: 'Persistencia', status: 'ready', records: 0, durationMs: null, error: null },
  ]);

  multiplierPresets: MultiplierPreset[] = [
    { key: 1, label: '1×' },
    { key: 2, label: '2×' },
    { key: 3, label: '3×' },
    { key: 4, label: '4×' },
  ];

  baseTrackCount = computed(() => this.summary()?.total_events ?? this.summary()?.total_streams ?? 0);
  totalEventCount = computed(() => this.summary()?.total_events ?? this.summary()?.total_streams ?? 0);

  targetTrackCount = computed(() => {
    if (this.volumeMode() === 'custom') return this.customTarget();
    return this.baseTrackCount() * this.selectedMultiplier();
  });

  tracksToCreate = computed(() => Math.max(0, this.targetTrackCount() - this.baseTrackCount()));

  estimatedDbMb = computed(() => {
    const total = this.targetTrackCount();
    return Math.max(1, Math.round((total * 0.25) / 1024));
  });

  volumeValidation = computed(() => {
    const lim = this.limits();
    const target = this.targetTrackCount();
    const delta = this.tracksToCreate();
    const maxTotal = lim?.max_target_total ?? 5_000_000;
    const maxRun = lim?.max_create_per_run ?? 2_000_000;
    const warnAbove = lim?.warn_create_above ?? 500_000;

    if (target > maxTotal) {
      return {
        ok: false,
        level: 'error' as const,
        message: `Máximo ${this.fmt(maxTotal)} registros en total (pediste ${this.fmt(target)}).`,
      };
    }
    if (delta > maxRun) {
      return {
        ok: false,
        level: 'error' as const,
        message: `Máximo ${this.fmt(maxRun)} por ejecución (generarías ${this.fmt(delta)}). Usa +100K varias veces.`,
      };
    }
    if (delta === 0) {
      return {
        ok: false,
        level: 'info' as const,
        message: 'El objetivo ya está cubierto — no hay nada que generar.',
      };
    }
    if (delta >= warnAbove || target >= 1_000_000) {
      return {
        ok: true,
        level: 'warn' as const,
        message: `Generación grande: +${this.fmt(delta)} eventos (~${this.estimatedDbMb()} MB). Puede tardar varios minutos.`,
      };
    }
    return { ok: true, level: 'ok' as const, message: '' };
  });

  canRunPipeline = computed(
    () =>
      this.apiConnected() &&
      this.pipelineState() !== 'running' &&
      (this.volumeValidation().ok || this.volumeValidation().level === 'info'),
  );

  /** Shown on disabled run/import controls so the reason is obvious without redesign. */
  runBlockedReason = computed(() => {
    if (this.pipelineState() === 'running') {
      return 'Pipeline en ejecución';
    }
    if (!this.apiConnected()) {
      return 'Sin conexión API — no se puede ejecutar el pipeline';
    }
    const vol = this.volumeValidation();
    if (!vol.ok && vol.level !== 'info' && vol.message) {
      return vol.message;
    }
    return '';
  });

  overallStateKey = computed<OverallStateKey>(() => {
    if (!this.apiConnected()) return 'offline';
    if (this.pipelineState() === 'running') return 'running';
    if (this.pipelineState() === 'failed' || this.lastError()) return 'failed';
    if (this.pipelineState() === 'completed') return 'completed';
    return 'idle';
  });

  overallStatusLabel = computed(() => {
    switch (this.overallStateKey()) {
      case 'offline':
        return 'Sin conexión';
      case 'running':
        return 'Procesando';
      case 'failed':
        return 'Requiere atención';
      case 'completed':
        return 'Completado';
      default:
        return 'Listo';
    }
  });

  lastExecutionLabel = computed(() => {
    const load = this.lastLoad();
    if (!load?.fecha_carga) return '—';
    return new Date(load.fecha_carga).toLocaleString('es-ES', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  });

  durationLabel = computed(() => {
    if (this.pipelineState() === 'running') {
      return this.formatDurationSec(this.elapsedSeconds());
    }
    const sec = this.lastRunDurationSec();
    if (sec == null || sec <= 0) return null;
    return this.formatDurationSec(sec);
  });

  lastUpdateLabel = computed(() => {
    const updated = this.summary()?.events_updated_at || this.lastLoad()?.fecha_carga;
    if (!updated) return null;
    return new Date(updated).toLocaleString('es-ES', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  });

  activeStageLabel = computed(() => {
    const running = this.timeline().find((s) => s.status === 'running');
    return running?.name ?? null;
  });

  ngOnInit() {
    this.refreshStatus();
  }

  ngOnDestroy() {
    this.clearTimers();
  }

  refreshStatus() {
    this.loadWarehouseKpis();
  }

  private loadWarehouseKpis() {
    this.isLoadingKpis.set(true);
    let pending = 4;
    const done = () => {
      if (--pending <= 0) this.isLoadingKpis.set(false);
    };

    this.stats.getSyntheticLimits().subscribe({
      next: (l) => {
        this.limits.set(l);
        done();
      },
      error: () => {
        this.limits.set({
          max_target_total: 5_000_000,
          max_create_per_run: 2_000_000,
          warn_create_above: 500_000,
          batch_size: 100_000,
          duckdb_note: 'DuckDB soporta millones de filas.',
        });
        done();
      },
    });

    this.stats.getSummary().subscribe({
      next: (d) => {
        this.summary.set(d);
        this.apiConnected.set(true);
        done();
      },
      error: () => {
        this.apiConnected.set(false);
        done();
      },
    });

    this.stats.getLastLoads(1).subscribe({
      next: (loads) => {
        this.lastLoad.set(loads?.[0] ?? null);
        done();
      },
      error: () => done(),
    });

    this.stats.getWarehouseStatus().subscribe({
      next: (w) => {
        if (typeof w.db_size_mb === 'number' && w.db_size_mb > 0) {
          this.warehouseSizeMb.set(w.db_size_mb);
        }
        if (w.last_load) this.lastLoad.set(w.last_load);
        if (w.recent_stages?.length) {
          const stageMap = new Map(w.recent_stages.map((s) => [s.stage, s]));
          this.timeline.update((steps) =>
            steps.map((step) => {
              const key =
                step.id === 'bronze'
                  ? 'load_staging'
                  : step.id === 'gold'
                    ? 'build_warehouse'
                    : step.id;
              const match = stageMap.get(key) ?? stageMap.get(step.id);
              if (!match) return step;
              const ok = (match.status || '').toUpperCase() === 'OK';
              return {
                ...step,
                records: match.rows_out > 0 ? match.rows_out : step.records,
                durationMs: match.duration_ms > 0 ? match.duration_ms : step.durationMs,
                status: ok ? ('success' as LayerStatus) : ('warning' as LayerStatus),
                error: ok ? null : 'Etapa con advertencias',
              };
            }),
          );
        }
        done();
      },
      error: () => done(),
    });
  }

  selectMultiplier(key: 1 | 2 | 3 | 4) {
    if (this.pipelineState() === 'running') return;
    this.volumeMode.set('multiplier');
    this.selectedMultiplier.set(key);
  }

  setVolumeMode(mode: VolumeMode) {
    if (this.pipelineState() === 'running') return;
    this.volumeMode.set(mode);
    if (mode === 'custom' && this.customTarget() <= this.baseTrackCount()) {
      this.customTarget.set(Math.max(this.baseTrackCount() + 1, 400_000));
    }
  }

  onCustomTargetInput(event: Event) {
    const raw = (event.target as HTMLInputElement).value.replace(/\s/g, '');
    const parsed = parseInt(raw, 10);
    if (!Number.isFinite(parsed) || parsed < 1) return;
    const max = this.limits()?.max_target_total ?? 5_000_000;
    this.customTarget.set(Math.min(parsed, max));
  }

  applyIncrement(amount = 100_000) {
    if (this.pipelineState() === 'running') return;
    const max = this.limits()?.max_target_total ?? 5_000_000;
    this.volumeMode.set('custom');
    this.customTarget.set(Math.min(this.baseTrackCount() + amount, max));
  }

  runPipeline() {
    if (this.pipelineState() === 'running') return;
    if (!this.apiConnected()) {
      this.addLog('WARN', this.i18n.t('elt.backendUnavailable'));
      return;
    }

    const validation = this.volumeValidation();
    if (!validation.ok && validation.level !== 'info') {
      this.addLog('WARN', validation.message);
      return;
    }
    if (validation.level === 'warn') {
      void this.confirm
        .open({
          title: this.i18n.t('confirm.continueTitle'),
          message: `${validation.message}\n\n${this.i18n.t('confirm.continuePrompt')}`,
          confirmLabel: this.i18n.t('common.continue'),
          cancelLabel: this.i18n.t('common.cancel'),
        })
        .then((ok) => {
          if (ok) this.executePipeline();
        });
      return;
    }

    this.executePipeline();
  }

  private executePipeline() {
    this.clearTimers();
    this.pipelineState.set('running');
    this.runProgress.set(5);
    this.logs.set([]);
    this.lastError.set(null);
    this.lastRunDurationSec.set(null);
    this.elapsedSeconds.set(0);
    this.runStartMs = Date.now();

    const target = this.targetTrackCount();

    this.addLog('INFO', 'Importando catálogo desde PocketBase…');
    this.timeline.update((s) =>
      s.map((l) => ({
        ...l,
        status: l.id === 'extract' ? ('running' as LayerStatus) : ('idle' as LayerStatus),
        error: null,
      })),
    );

    this.elapsedTimer = setInterval(() => {
      this.elapsedSeconds.set(Math.floor((Date.now() - this.runStartMs) / 1000));
    }, 500);

    this.stats.importFromPocketBase().subscribe({
      next: (res) => {
        const loaded = res.rows_loaded ?? 0;
        const elapsedMs = Math.round((res.elapsed_s ?? 0) * 1000);
        this.runProgress.set(55);
        this.addLog(
          'SUCCESS',
          `${this.fmt(loaded)} pistas cargadas desde ${this.humanSource(res.source)}`,
        );
        this.timeline.update((layers) =>
          layers.map((l) => {
            if (l.id === 'extract' || l.id === 'bronze') {
              return {
                ...l,
                records: loaded || l.records,
                durationMs: elapsedMs || l.durationMs,
                status: 'success' as LayerStatus,
              };
            }
            if (l.id === 'silver' || l.id === 'gold' || l.id === 'warehouse') {
              return { ...l, status: 'running' as LayerStatus };
            }
            return l;
          }),
        );
        this.stats.getSummary().subscribe({
          next: (fresh) => {
            this.summary.set(fresh);
            const baseEvents = fresh.total_events ?? fresh.total_streams ?? 0;
            const delta = Math.max(0, target - baseEvents);
            if (delta > 0) {
              this.addLog(
                'INFO',
                `Expandiendo actividad: ${this.fmt(baseEvents)} → ${this.fmt(target)} (+${this.fmt(delta)})`,
              );
              this.persistSynthetic(target);
            } else {
              this.addLog('INFO', 'Sin expansión — el volumen ya cubre el objetivo');
              this.completePipeline(baseEvents, 0);
            }
          },
          error: () => this.failPipeline({}, 'Persistencia', 'No se pudo leer el estado tras la importación.'),
        });
      },
      error: (err) =>
        this.failPipeline(err, 'Extracción', 'No se pudo importar el catálogo desde PocketBase.'),
    });
  }

  importFromPocketBaseOnly() {
    if (this.pipelineState() === 'running') return;
    if (!this.apiConnected()) {
      this.addLog('WARN', this.i18n.t('elt.backendUnavailable'));
      return;
    }

    this.clearTimers();
    this.pipelineState.set('running');
    this.runProgress.set(0);
    this.logs.set([]);
    this.lastError.set(null);
    this.runStartMs = Date.now();
    this.elapsedSeconds.set(0);
    this.addLog('INFO', 'Importando solo catálogo desde PocketBase…');
    this.timeline.update((s) =>
      s.map((l) => ({
        ...l,
        status: l.id === 'extract' ? ('running' as LayerStatus) : ('idle' as LayerStatus),
        error: null,
      })),
    );

    this.elapsedTimer = setInterval(() => {
      this.elapsedSeconds.set(Math.floor((Date.now() - this.runStartMs) / 1000));
    }, 500);

    this.stats.importFromPocketBase().subscribe({
      next: (res) => {
        const loaded = res.rows_loaded ?? 0;
        this.timeline.update((layers) =>
          layers.map((l) => ({
            ...l,
            records: ['extract', 'bronze', 'warehouse'].includes(l.id) ? loaded || l.records : l.records,
            status: 'success' as LayerStatus,
          })),
        );
        this.stats.getSummary().subscribe({
          next: (fresh) => {
            this.summary.set(fresh);
            this.completePipeline(fresh.total_events ?? fresh.total_streams ?? loaded, 0);
          },
          error: () => this.completePipeline(loaded, 0),
        });
        this.stats.getLastLoads(1).subscribe({
          next: (loads) => this.lastLoad.set(loads?.[0] ?? null),
        });
      },
      error: (err) =>
        this.failPipeline(err, 'Extracción', 'No se pudo importar el catálogo desde PocketBase.'),
    });
  }

  private failPipeline(
    err: { error?: { detail?: unknown } },
    stage: string,
    fallback: string,
  ) {
    const detail = err?.error?.detail;
    const raw =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ')
          : '';
    const message = this.humanizeError(raw) || fallback;
    const time = new Date().toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    this.addLog('WARN', message);
    this.lastError.set({ stage: `${stage} requiere atención`, message, time });
    this.pipelineState.set('failed');
    this.timeline.update((steps) =>
      steps.map((s) =>
        s.name === stage || (stage === 'Extracción' && s.id === 'extract')
          ? { ...s, status: 'failed' as LayerStatus, error: message }
          : s.status === 'running'
            ? { ...s, status: 'idle' as LayerStatus }
            : s,
      ),
    );
    this.lastRunDurationSec.set(Math.floor((Date.now() - this.runStartMs) / 1000));
    this.clearTimers();
  }

  private persistSynthetic(target: number) {
    if (this.runTimer) {
      clearInterval(this.runTimer);
      this.runTimer = null;
    }
    this.runProgress.set(98);

    const delta = this.tracksToCreate();
    if (delta <= 0) {
      this.addLog('INFO', `Ya hay ${this.fmt(this.baseTrackCount())} registros — objetivo alcanzado`);
      this.completePipeline(this.baseTrackCount(), 0);
      return;
    }

    this.timeline.update((layers) =>
      layers.map((l) =>
        l.id === 'silver' || l.id === 'gold' || l.id === 'warehouse'
          ? { ...l, status: 'running' as LayerStatus }
          : l,
      ),
    );

    this.stats.generateSynthetic({ target_total: target }).subscribe({
      next: (res) => {
        this.summary.update((s) =>
          s
            ? {
                ...s,
                total_events: res.after,
                total_tracks: res.track_total ?? s.total_tracks,
              }
            : s,
        );
        if (res.purged_synthetic_tracks) {
          this.addLog(
            'WARN',
            `${this.fmt(res.purged_synthetic_tracks)} pistas sintéticas antiguas eliminadas del catálogo`,
          );
        }
        this.addLog(
          'SUCCESS',
          `+${res.created.toLocaleString('es-ES')} eventos generados (${this.fmt(res.before)} → ${this.fmt(res.after)})`,
        );
        this.timeline.update((layers) =>
          layers.map((l) => ({
            ...l,
            records:
              l.id === 'silver' || l.id === 'gold' || l.id === 'warehouse'
                ? res.after || l.records
                : l.records,
            status: 'success' as LayerStatus,
          })),
        );
        this.completePipeline(res.after, res.created);
        this.stats.getLastLoads(1).subscribe({
          next: (loads) => this.lastLoad.set(loads?.[0] ?? null),
        });
      },
      error: (err) =>
        this.failPipeline(
          err,
          'Transformación',
          'No se pudo completar la expansión de actividad analítica.',
        ),
    });
  }

  private completePipeline(total: number, created: number) {
    this.clearTimers();
    this.runProgress.set(100);
    this.pipelineState.set('completed');
    this.lastError.set(null);
    this.lastRunDurationSec.set(Math.floor((Date.now() - this.runStartMs) / 1000));
    this.timeline.update((l) =>
      l.map((s) => ({ ...s, status: 'success' as LayerStatus, error: null })),
    );
    this.addLog('SUCCESS', `Pipeline completado — ${this.fmt(total)} eventos en el almacén`);
    if (created > 0) {
      this.lastLoad.set({
        fecha_carga: new Date().toISOString(),
        modo: `synthetic_activity_target_${this.targetTrackCount()}`,
        registros_nuevos: created,
        total_raw: total,
        estado: 'OK',
      });
    }
    this.refreshStatus();
  }

  private addLog(level: LogLevel, message: string) {
    const time = new Date().toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    this.logs.update((logs) => [...logs, { time, level, message }]);
  }

  private clearTimers() {
    if (this.runTimer) {
      clearInterval(this.runTimer);
      this.runTimer = null;
    }
    if (this.elapsedTimer) {
      clearInterval(this.elapsedTimer);
      this.elapsedTimer = null;
    }
  }

  private humanSource(source: string | null | undefined): string {
    const s = (source || '').toLowerCase();
    if (s.includes('pocketbase')) return 'PocketBase';
    if (!s) return 'la fuente configurada';
    return source!;
  }

  private humanizeError(raw: string): string {
    const t = (raw || '').trim();
    if (!t) return '';
    if (/stack|traceback|exception at|typeerror|referenceerror/i.test(t)) {
      return 'No se pudo completar la operación. Revisa la conexión e inténtalo de nuevo.';
    }
    return t.length > 220 ? `${t.slice(0, 217)}…` : t;
  }

  fmt(val?: number): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toLocaleString('es-ES');
  }

  statusLabel(status: LayerStatus): string {
    switch (status) {
      case 'ready':
      case 'idle':
        return 'Pendiente';
      case 'running':
        return 'En ejecución';
      case 'success':
        return 'Completado';
      case 'warning':
        return 'Con advertencias';
      case 'failed':
        return 'Fallido';
      default: {
        const _exhaustive: never = status;
        return _exhaustive;
      }
    }
  }

  formatDurationMs(ms: number): string {
    if (ms < 1000) return `${ms} ms`;
    return this.formatDurationSec(Math.round(ms / 1000));
  }

  formatDurationSec(sec: number): string {
    if (sec < 60) return `${sec}s`;
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return s ? `${m}m ${s}s` : `${m}m`;
  }
}
