import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-enterprise-stat-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="kpi-card ent-stat">
      <h3 class="ent-stat__label">{{ label() }}</h3>
      @if (isNull()) {
        <p class="kpi-null ent-stat__null">{{ displayNull() }}</p>
      } @else {
        <p class="kpi-value ent-stat__value">{{ value() }}</p>
      }
      @if (hint()) {
        <p class="kpi-source ent-stat__hint">{{ hint() }}</p>
      }
    </article>
  `,
})
export class EnterpriseStatCardComponent {
  readonly label = input.required<string>();
  readonly value = input<string | number | null | undefined>(null);
  readonly hint = input<string | undefined>();
  readonly nullLabel = input<string | undefined>();

  readonly isNull = computed(() => {
    const v = this.value();
    return v === null || v === undefined || v === '';
  });

  readonly displayNull = computed(() => this.nullLabel() ?? 'No disponible');
}
