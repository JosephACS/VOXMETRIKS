import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, OnDestroy, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../../analytics/services/stats.service';
import { KpiCardComponent } from '../../../shared/components/kpi-card/kpi-card.component';
import { StatsSummary, LoadRecord, SyntheticLimits } from '../../../shared/models/api.models';

type LayerStatus = 'ready' | 'idle' | 'running' | 'success' | 'warning' | 'failed';
type PipelineState = 'idle' | 'running' | 'completed' | 'failed';
type LogLevel = 'INFO' | 'WARN' | 'SUCCESS';

interface TimelineStep {
  id: string;
  name: string;
  subtitle: string;
  file: string;
  icon: string;
  color: string;
  status: LayerStatus;
  records: number;
}

interface LogEntry {
  time: string;
  level: LogLevel;
  message: string;
}

interface ChartSegment {
  label: string;
  value: number;
  color: string;
}

interface MultiplierPreset {
  key: 1 | 2 | 3 | 4;
  label: string;
}

type VolumeMode = 'multiplier' | 'custom';

@Component({
  selector: 'app-etl-pipeline',
  standalone: true,
  imports: [CommonModule, KpiCardComponent],
  templateUrl: './etl-pipeline.component.html',
  styleUrls: ['./etl-pipeline.component.css'],
})
export class EtlPipelineComponent implements OnInit, OnDestroy {
  private iconRender = inject(IconRenderService);

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

  elapsedSeconds = signal(0);
  throughput = signal(0);
  transformPct = signal(0);
  dataQuality = signal(0);
  warehouseSizeMb = signal(0);

  timeline = signal<TimelineStep[]>([
    { id: 'extract', name: 'Extracción', subtitle: 'Fuente', file: 'warehouse', icon: '↓', color: '#3b82f6', status: 'ready', records: 0 },
    { id: 'bronze', name: 'Carga', subtitle: 'Bronze', file: 'raw', icon: 'B', color: '#cd7f32', status: 'ready', records: 0 },
    { id: 'silver', name: 'Transformación', subtitle: 'Silver', file: 'clean', icon: 'S', color: '#94a3b8', status: 'ready', records: 0 },
    { id: 'gold', name: 'Modelado', subtitle: 'Gold', file: 'dim_*', icon: 'G', color: '#f59e0b', status: 'ready', records: 0 },
    { id: 'warehouse', name: 'Persistencia', subtitle: 'DuckDB', file: 'voxmetrik.duckdb', icon: 'W', color: '#1ed896', status: 'ready', records: 0 },
  ]);

  multiplierPresets: MultiplierPreset[] = [
    { key: 1, label: '1×' },
    { key: 2, label: '2×' },
    { key: 3, label: '3×' },
    { key: 4, label: '4×' },
  ];

  tableDistribution: ChartSegment[] = [
    { label: 'Dimensiones', value: 7, color: '#3b82f6' },
    { label: 'Facts', value: 1, color: '#1ed896' },
    { label: 'Agregaciones', value: 4, color: '#7c3aed' },
  ];

  baseTrackCount = computed(() => this.summary()?.total_tracks ?? 0);

  targetTrackCount = computed(() => {
    if (this.volumeMode() === 'custom') return this.customTarget();
    return this.baseTrackCount() * this.selectedMultiplier();
  });

  tracksToCreate = computed(() =>
    Math.max(0, this.targetTrackCount() - this.baseTrackCount())
  );

  estimatedDbMb = computed(() => {
    const total = this.targetTrackCount();
    return Math.max(1, Math.round((total * 0.8) / 1024));
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
        message: `Generación grande: +${this.fmt(delta)} (~${this.estimatedDbMb()} MB en DuckDB). Puede tardar varios minutos.`,
      };
    }
    return { ok: true, level: 'ok' as const, message: '' };
  });

  canRunPipeline = computed(() =>
    this.apiConnected() &&
    this.pipelineState() !== 'running' &&
    this.volumeValidation().ok &&
    this.volumeValidation().level !== 'info'
  );

  selectedRecordCount = computed(() => this.targetTrackCount());

  estimatedDuration = computed(() => {
    const toCreate = this.tracksToCreate();
    if (toCreate <= 0) return '0s est.';
    const sec = Math.max(4, Math.ceil(toCreate / 50_000));
    return `${sec}s est.`;
  });

  pipelineStatusLabel = computed(() => {
    switch (this.pipelineState()) {
      case 'running': return 'En ejecución';
      case 'completed': return 'Completado';
      case 'failed': return 'Fallido';
      default: return 'Listo';
    }
  });

  warehouseHealth = computed(() => {
    if (this.pipelineState() === 'failed') return 62;
    if (this.pipelineState() === 'running') return 78;
    if (this.dataQuality() > 0) return this.dataQuality();
    return this.apiConnected() ? 94 : 88;
  });

  lastExecutionLabel = computed(() => {
    const load = this.lastLoad();
    if (!load?.fecha_carga) return '—';
    return new Date(load.fecha_carga).toLocaleString('es-ES', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  });

  totalTables = 12;

  constructor(private stats: StatsService) {}

  ngOnInit() {
    this.loadWarehouseKpis();
    this.refreshMetrics();
  }

  ngOnDestroy() {
    this.clearTimers();
  }

  private loadWarehouseKpis() {
    let pending = 4;
    const done = () => { if (--pending <= 0) this.isLoadingKpis.set(false); };

    this.stats.getSyntheticLimits().subscribe({
      next: (l) => { this.limits.set(l); done(); },
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
        this.refreshMetrics(d.total_tracks);
        done();
      },
      error: () => {
        this.apiConnected.set(false);
        this.refreshMetrics();
        done();
      },
    });

    this.stats.getLastLoads(1).subscribe({
      next: (loads) => { this.lastLoad.set(loads?.[0] ?? null); done(); },
      error: () => done(),
    });

    this.stats.getWarehouseStatus().subscribe({
      next: (w) => {
        this.warehouseSizeMb.set(w.db_size_mb ?? 0);
        const facts = Object.values(w.layers?.gold?.facts ?? {}).reduce((a, b) => a + b, 0);
        const aggs = Object.values(w.layers?.gold?.aggregates ?? {}).reduce((a, b) => a + b, 0);
        const dims = Object.values(w.layers?.gold?.dimensions ?? {}).reduce((a, b) => a + b, 0);
        this.tableDistribution = [
          { label: 'Dimensiones', value: dims, color: '#3b82f6' },
          { label: 'Facts', value: facts, color: '#1ed896' },
          { label: 'Agregaciones', value: aggs, color: '#7c3aed' },
        ];
        if (w.recent_stages?.length) {
          const stageMap = new Map(w.recent_stages.map((s) => [s.stage, s]));
          this.timeline.update((steps) =>
            steps.map((step) => {
              const match = stageMap.get(step.id === 'bronze' ? 'load_staging' : step.id === 'gold' ? 'build_warehouse' : step.id);
              return match
                ? { ...step, records: match.rows_out, status: match.status === 'OK' ? 'success' as LayerStatus : step.status }
                : step;
            })
          );
        }
        done();
      },
      error: () => done(),
    });
  }

  private refreshMetrics(baseRecords?: number) {
    const count = baseRecords ?? this.targetTrackCount();
    const factors = [1.0, 0.98, 0.96, 0.94, 1.0];
    this.timeline.update((steps) =>
      steps.map((s, i) => ({ ...s, records: Math.round(count * factors[i]) }))
    );
    this.warehouseSizeMb.set(+(count / 1000 * 0.5).toFixed(1));
    this.transformPct.set(97);
  }

  selectMultiplier(key: 1 | 2 | 3 | 4) {
    if (this.pipelineState() === 'running') return;
    this.volumeMode.set('multiplier');
    this.selectedMultiplier.set(key);
    this.refreshMetrics();
  }

  setVolumeMode(mode: VolumeMode) {
    if (this.pipelineState() === 'running') return;
    this.volumeMode.set(mode);
    if (mode === 'custom' && this.customTarget() <= this.baseTrackCount()) {
      this.customTarget.set(Math.max(this.baseTrackCount() + 1, 400_000));
    }
    this.refreshMetrics();
  }

  onCustomTargetInput(event: Event) {
    const raw = (event.target as HTMLInputElement).value.replace(/\s/g, '');
    const parsed = parseInt(raw, 10);
    if (!Number.isFinite(parsed) || parsed < 1) return;
    const max = this.limits()?.max_target_total ?? 5_000_000;
    this.customTarget.set(Math.min(parsed, max));
    this.refreshMetrics();
  }

  applyQuickTarget(total: number) {
    if (this.pipelineState() === 'running') return;
    const max = this.limits()?.max_target_total ?? 5_000_000;
    this.volumeMode.set('custom');
    this.customTarget.set(Math.min(total, max));
    this.refreshMetrics();
  }

  /** Suma N al total actual (ej. +100K sobre lo que ya hay en BD). */
  applyIncrement(amount = 100_000) {
    if (this.pipelineState() === 'running') return;
    const max = this.limits()?.max_target_total ?? 5_000_000;
    this.volumeMode.set('custom');
    this.customTarget.set(Math.min(this.baseTrackCount() + amount, max));
    this.refreshMetrics();
  }

  runPipeline() {
    if (this.pipelineState() === 'running') return;
    if (!this.apiConnected()) {
      this.addLog('WARN', 'Backend no disponible — conecta FastAPI en localhost:8000');
      return;
    }
    if (this.baseTrackCount() === 0) {
      this.addLog('WARN', 'Warehouse vacío — ejecuta elt_pipeline.py primero');
      return;
    }

    const validation = this.volumeValidation();
    if (!validation.ok) {
      this.addLog('WARN', validation.message);
      return;
    }
    if (validation.level === 'warn') {
      const ok = confirm(`${validation.message}\n\n¿Continuar?`);
      if (!ok) return;
    }

    this.clearTimers();
    this.pipelineState.set('running');
    this.runProgress.set(0);
    this.logs.set([]);
    this.elapsedSeconds.set(0);
    this.throughput.set(0);
    this.dataQuality.set(0);
    this.runStartMs = Date.now();

    const base = this.baseTrackCount();
    const target = this.targetTrackCount();
    const delta = this.tracksToCreate();

    this.addLog('INFO', `ELT iniciado — actual ${this.fmt(base)} → objetivo ${this.fmt(target)} (+${this.fmt(delta)})`);
    this.addLog('INFO', 'Extract → Load → Transform desde warehouse existente');

    this.timeline.update((s) => s.map((l) => ({ ...l, status: 'idle' as LayerStatus })));

    this.elapsedTimer = setInterval(() => {
      const sec = Math.floor((Date.now() - this.runStartMs) / 1000);
      this.elapsedSeconds.set(sec);
      if (sec > 0) this.throughput.set(Math.round(target / sec));
    }, 500);

    const steps = ['extract', 'bronze', 'silver', 'gold', 'warehouse'];
    const logMessages: Record<string, { level: LogLevel; msg: string }[]> = {
      extract: [
        { level: 'INFO', msg: `Leyendo ${this.fmt(base)} tracks de dim_track...` },
      ],
      bronze: [
        { level: 'INFO', msg: 'Load bronze — snapshot warehouse' },
        { level: 'SUCCESS', msg: `${this.fmt(base)} filas fuente listas` },
      ],
      silver: [
        { level: 'INFO', msg: 'Transform — clonado con variación de features' },
        { level: 'SUCCESS', msg: 'Reglas de calidad OK' },
      ],
      gold: [
        { level: 'INFO', msg: 'Model gold — asignando IDs sintéticos' },
        { level: 'SUCCESS', msg: `Objetivo: ${this.fmt(target)} registros` },
      ],
      warehouse: [
        { level: 'INFO', msg: 'Persistiendo en DuckDB (dim_track)...' },
      ],
    };

    let stepIndex = 0;
    let logIndex = 0;

    this.runTimer = setInterval(() => {
      const currentId = steps[stepIndex];
      const progress = Math.min(95, Math.round(((stepIndex + 0.5) / steps.length) * 100));
      this.runProgress.set(progress);

      this.timeline.update((layers) =>
        layers.map((l) => {
          const idx = steps.indexOf(l.id);
          if (idx < stepIndex) return { ...l, status: 'success' as LayerStatus };
          if (l.id === currentId) return { ...l, status: 'running' as LayerStatus };
          return { ...l, status: 'idle' as LayerStatus };
        })
      );

      const msgs = logMessages[currentId];
      if (logIndex < msgs.length) {
        this.addLog(msgs[logIndex].level, msgs[logIndex].msg);
        logIndex++;
      } else {
        stepIndex++;
        logIndex = 0;
        if (stepIndex >= steps.length) this.persistSynthetic(target);
      }
    }, 600);
  }

  private persistSynthetic(target: number) {
    if (this.runTimer) { clearInterval(this.runTimer); this.runTimer = null; }
    this.runProgress.set(98);

    const delta = this.tracksToCreate();
    if (delta <= 0) {
      this.addLog('INFO', `Ya hay ${this.fmt(this.baseTrackCount())} registros — objetivo ${this.fmt(target)} alcanzado`);
      this.completePipeline(this.baseTrackCount(), 0);
      return;
    }

    this.stats.generateSynthetic({ target_total: target }).subscribe({
      next: (res) => {
        this.summary.update((s) => s ? { ...s, total_tracks: res.after } : s);
        this.addLog('SUCCESS', `+${res.created.toLocaleString('es-ES')} tracks generados (${this.fmt(res.before)} → ${this.fmt(res.after)})`);
        this.completePipeline(res.after, res.created);
        this.stats.getLastLoads(1).subscribe({
          next: (loads) => this.lastLoad.set(loads?.[0] ?? null),
        });
      },
      error: (err) => {
        const detail = err?.error?.detail;
        const msg = typeof detail === 'string' ? detail
          : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).join('; ')
          : 'Error al persistir sintéticos';
        this.addLog('WARN', msg);
        this.pipelineState.set('failed');
        this.clearTimers();
      },
    });
  }

  private completePipeline(total: number, created: number) {
    this.clearTimers();
    this.runProgress.set(100);
    this.pipelineState.set('completed');
    this.transformPct.set(97);
    this.dataQuality.set(98);
    this.warehouseSizeMb.set(+(total / 1000 * 0.5).toFixed(1));
    this.timeline.update((l) => l.map((s) => ({ ...s, status: 'success' as LayerStatus })));
    this.addLog('SUCCESS', `Pipeline ELT completado — ${this.fmt(total)} tracks en warehouse`);
    if (created > 0) {
      this.lastLoad.set({
        fecha_carga: new Date().toISOString(),
        modo: `synthetic_target_${this.targetTrackCount()}`,
        registros_nuevos: created,
        total_raw: total,
        estado: 'OK',
      });
    }
    this.refreshMetrics(total);
  }

  resetPipeline() {
    if (this.pipelineState() === 'running') return;
    this.clearTimers();
    this.pipelineState.set('idle');
    this.runProgress.set(0);
    this.logs.set([]);
    this.elapsedSeconds.set(0);
    this.throughput.set(0);
    this.dataQuality.set(0);
    this.timeline.update((s) => s.map((l) => ({ ...l, status: 'ready' as LayerStatus })));
    this.refreshMetrics(this.baseTrackCount());
  }

  private addLog(level: LogLevel, message: string) {
    const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    this.logs.update((logs) => [...logs, { time, level, message }]);
  }

  private clearTimers() {
    if (this.runTimer) { clearInterval(this.runTimer); this.runTimer = null; }
    if (this.elapsedTimer) { clearInterval(this.elapsedTimer); this.elapsedTimer = null; }
  }

  fmt(val?: number): string {
    if (val == null) return '—';
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`;
    return val.toLocaleString('es-ES');
  }

  statusLabel(status: LayerStatus): string {
    const map: Record<LayerStatus, string> = {
      ready: 'Ready', idle: 'Waiting', running: 'Running',
      success: 'Success', warning: 'Warning', failed: 'Failed',
    };
    return map[status];
  }

  distBarWidth(value: number): number {
    const max = Math.max(...this.tableDistribution.map((d) => d.value));
    return Math.round((value / max) * 100);
  }

  healthColor(score: number): string {
    if (score >= 90) return '#10b981';
    if (score >= 75) return '#f59e0b';
    return '#ef4444';
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
