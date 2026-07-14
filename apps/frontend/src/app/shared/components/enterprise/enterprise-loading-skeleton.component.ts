import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-enterprise-loading-skeleton',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="vx-skel-block ent-skel" aria-busy="true" aria-live="polite">
      @for (_ of rowList(); track $index) {
        <div class="vx-skel"></div>
      }
    </div>
  `,
})
export class EnterpriseLoadingSkeletonComponent {
  readonly rows = input(3);

  readonly rowList = computed(() => {
    const n = Math.max(1, this.rows());
    return Array.from({ length: n }, (_, i) => i);
  });
}
