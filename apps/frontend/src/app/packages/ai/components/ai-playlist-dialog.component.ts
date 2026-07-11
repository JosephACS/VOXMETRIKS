import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AIService } from '../services/ai.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-ai-playlist-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    @if (open()) {
      <div class="ai-dialog-backdrop" (click)="close()">
        <div class="ai-dialog" role="dialog" (click)="$event.stopPropagation()">
          <h2>Crear playlist con IA</h2>
          <p class="hint">Describe lo que quieres escuchar. No se guardará hasta que confirmes.</p>
          <textarea
            [(ngModel)]="prompt"
            rows="3"
            placeholder="Ej: playlist energética para entrenar"
            [disabled]="loading()"
          ></textarea>
          @if (!preview()) {
            <button type="button" class="btn-primary" [disabled]="loading() || prompt.trim().length < 3" (click)="generate()">
              {{ loading() ? 'Generando…' : 'Generar preview' }}
            </button>
          } @else {
            <div class="preview">
              <h3>{{ preview()!.name }}</h3>
              <p>{{ preview()!.description }}</p>
              <p class="meta">{{ preview()!.track_count }} canciones · {{ preview()!.provider ?? 'local' }}</p>
              <ul>
                @for (t of preview()!.tracks.slice(0, 8); track t.id_track) {
                  <li>{{ t.nombre_track }} — {{ t.nombre_artista ?? '—' }}</li>
                }
              </ul>
            </div>
            <div class="actions">
              <button type="button" class="btn-secondary" (click)="preview.set(null)">Volver</button>
              <button type="button" class="btn-primary" [disabled]="saving()" (click)="confirm()">
                {{ saving() ? 'Guardando…' : 'Confirmar y guardar' }}
              </button>
            </div>
          }
          <button type="button" class="close" (click)="close()">×</button>
        </div>
      </div>
    }
  `,
  styles: [`
    .ai-dialog-backdrop {
      position: fixed; inset: 0; z-index: 9999;
      background: rgba(0,0,0,0.55);
      display: flex; align-items: center; justify-content: center;
    }
    .ai-dialog {
      position: relative;
      width: min(480px, 92vw);
      padding: 1.25rem;
      border-radius: 12px;
      background: #121218;
      border: 1px solid rgba(255,255,255,0.08);
    }
    textarea {
      width: 100%; margin: 0.75rem 0;
      padding: 0.65rem; border-radius: 8px;
      background: #1a1a22; color: #eee; border: 1px solid #333;
    }
    .hint { font-size: 0.85rem; color: #9ca3af; }
    .preview ul { max-height: 160px; overflow: auto; font-size: 0.85rem; color: #ccc; }
    .actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
    .btn-primary, .btn-secondary {
      padding: 0.5rem 1rem; border-radius: 8px; border: none; cursor: pointer;
    }
    .btn-primary { background: #1ed896; color: #000; }
    .btn-secondary { background: #333; color: #eee; }
    .close { position: absolute; top: 0.5rem; right: 0.75rem; background: none; border: none; color: #888; font-size: 1.25rem; cursor: pointer; }
    .meta { font-size: 0.8rem; color: #888; }
  `],
})
export class AiPlaylistDialogComponent {
  private readonly ai = inject(AIService);
  private readonly notify = inject(NotificationService);

  readonly open = signal(false);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly preview = signal<import('../services/ai.service').PlaylistPreview | null>(null);
  prompt = '';

  show(): void {
    this.open.set(true);
    this.preview.set(null);
    this.prompt = '';
  }

  close(): void {
    this.open.set(false);
  }

  generate(): void {
    this.loading.set(true);
    this.ai.previewPlaylist(this.prompt.trim()).subscribe({
      next: (p) => { this.preview.set(p); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.notify.error('No se pudo generar la playlist', 'Intenta con otra descripción.');
      },
    });
  }

  confirm(): void {
    const p = this.preview();
    if (!p?.tracks?.length) return;
    this.saving.set(true);
    const ids = p.tracks.map((t) => t.id_track);
    this.ai.confirmPlaylist(p.name, p.description, ids).subscribe({
      next: () => {
        this.saving.set(false);
        this.notify.success('Playlist creada', p.name);
        this.close();
      },
      error: () => {
        this.saving.set(false);
        this.notify.error('Error al guardar', 'Revisa tu sesión e intenta de nuevo.');
      },
    });
  }
}
