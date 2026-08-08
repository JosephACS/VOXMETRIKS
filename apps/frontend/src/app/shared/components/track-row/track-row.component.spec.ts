import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { provideRouter, RouterModule } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { TrackRowComponent } from './track-row.component';
import { DeferVisibleDirective } from '../../directives/defer-visible.directive';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlaybackStore } from '../../../playback-core/playback.store';
import { CoverArtService } from '../../services/cover-art.service';
import { TrackCoverService } from '../../services/track-cover.service';
import { PlayableTrack } from '../../models/player.models';

/**
 * Stub nested actions only. TrackRow keeps its productive inline template
 * (including `.tr-unavailable`) — we do not recreate that markup here.
 */
@Component({
  standalone: true,
  selector: 'app-track-actions',
  template: '',
})
class StubTrackActionsComponent {
  @Input() track: unknown;
  @Input() queue: unknown;
  @Input() artistId: unknown;
  @Input() size: unknown;
}

function sampleTrack(): PlayableTrack {
  return {
    id: 10,
    title: 'Song',
    artist: 'Artist',
    durationMs: 120_000,
    audioUrl: '',
    coverGradient: 'linear-gradient(#111,#222)',
  };
}

describe('TrackRowComponent Fuente no disponible (real template)', () => {
  let fixture: ComponentFixture<TrackRowComponent>;

  beforeEach(async () => {
    // Replace nested imports only — leave TrackRow template/styles untouched.
    TestBed.overrideComponent(TrackRowComponent, {
      set: {
        imports: [CommonModule, RouterModule, StubTrackActionsComponent, DeferVisibleDirective],
      },
    });

    await TestBed.configureTestingModule({
      imports: [TrackRowComponent],
      providers: [
        provideRouter([]),
        { provide: PlayerController, useValue: { playTrack: vi.fn() } },
        {
          provide: PlaybackStore,
          useValue: {
            isCurrentTrack: () => false,
            isPlaying: () => false,
            formatTime: (s: number) => {
              const m = Math.floor(s / 60);
              const sec = Math.floor(s % 60);
              return `${m}:${String(sec).padStart(2, '0')}`;
            },
          },
        },
        {
          provide: CoverArtService,
          useValue: { initialsFor: () => 'SA', gradientFor: () => 'g' },
        },
        { provide: TrackCoverService, useValue: { bestCover$: () => of(null) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TrackRowComponent);
    fixture.componentInstance.track = sampleTrack();
    fixture.componentInstance.index = 1;
  });

  it('renders productive .tr-unavailable badge from real template', () => {
    fixture.componentInstance.sourceUnavailable = true;
    fixture.detectChanges();

    const el = fixture.debugElement.query(By.css('.tr-unavailable'));
    expect(el).toBeTruthy();
    expect(el.nativeElement.textContent).toContain('Fuente no disponible');
    expect(fixture.nativeElement.textContent).toContain('Song');
    expect(fixture.nativeElement.textContent).toContain('Artist');
  });

  it('hides unavailable badge when source is available', () => {
    fixture.componentInstance.sourceUnavailable = false;
    fixture.componentInstance.energy = 0.4;
    fixture.detectChanges();

    expect(fixture.debugElement.query(By.css('.tr-unavailable'))).toBeNull();
    expect(fixture.debugElement.query(By.css('.tr-meta'))).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Energía');
  });
});
