import { Component, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { I18nService } from '../../../../core/services/i18n.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { StatsSummary } from '../../../../shared/models/api.models';
import { fmtNumber } from '../home-format.util';

@Component({
  selector: 'app-home-hero',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  templateUrl: './home-hero.component.html',
  styleUrls: ['../home.component.css'],
})
export class HomeHeroComponent {
  readonly lang = inject(I18nService).lang;

  readonly greetingKey = input.required<string>();
  readonly userName = input.required<string>();
  readonly userPlan = input.required<string>();
  readonly summary = input<StatsSummary | null>(null);
  readonly summaryLoading = input(false);
  readonly playlistCount = input(0);
  readonly listenStreak = input(0);
  readonly listenMinutesToday = input(0);
  readonly weeklyGoalPct = input(0);
  readonly explorerLevel = input(1);
  readonly heroStatSkels = input<number[]>([1, 2, 3, 4, 5]);

  fmt = fmtNumber;
}
