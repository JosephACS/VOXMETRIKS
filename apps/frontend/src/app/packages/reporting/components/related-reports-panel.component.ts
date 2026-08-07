import { Component, Input, OnChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import {
  SimpleReportCatalogItem,
  SimpleReportsApiService,
} from '../../simple-reports/services/simple-reports-api.service';

/** Spec 040 — contextual related reports for an enterprise module. */
@Component({
  selector: 'app-related-reports-panel',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    @if (items.length) {
      <section class="related" aria-label="Reportes relacionados">
        <h2 class="related__title">Reportes relacionados</h2>
        <p class="related__sub">{{ moduleLabel }} · abrir en el centro de reportes (mismo motor).</p>
        <ul class="related__list">
          @for (r of items; track r.id) {
            <li>
              <a [routerLink]="['/simple-reports']" [queryParams]="{ report: r.id, module: moduleId, context: moduleId, from: 'workpanel' }">
                {{ r.title }}
              </a>
              <span class="tag">{{ r.category }}</span>
            </li>
          }
        </ul>
        <a class="related__all" [routerLink]="['/simple-reports']" [queryParams]="{ module: moduleId, context: moduleId, from: 'workpanel' }">
          Ver todos en el centro
        </a>
      </section>
    }
  `,
  styles: [
    `
      .related {
        margin: 1.25rem 0;
        padding: 1rem;
        border: 1px solid var(--border-color, #ddd);
        border-radius: 0.4rem;
      }
      .related__title { margin: 0 0 0.35rem; font-size: 1.1rem; }
      .related__sub { margin: 0 0 0.75rem; opacity: 0.8; font-size: 0.9rem; }
      .related__list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.45rem; }
      .related__list li { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: baseline; }
      .tag { font-size: 0.75rem; opacity: 0.75; }
      .related__all { display: inline-block; margin-top: 0.75rem; font-weight: 600; }
    `,
  ],
})
export class RelatedReportsPanelComponent implements OnChanges {
  private readonly api = inject(SimpleReportsApiService);

  @Input() moduleId = 'control_decision';
  @Input() moduleLabel = 'Control y decisión';
  @Input() limit = 6;

  items: SimpleReportCatalogItem[] = [];

  ngOnChanges(): void {
    if (!this.moduleId) return;
    this.api.catalog({ module: this.moduleId }).subscribe({
      next: (res) => {
        this.items = (res.items || []).slice(0, this.limit);
      },
      error: () => {
        this.items = [];
      },
    });
  }
}
