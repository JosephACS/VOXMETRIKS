import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';
import { ProfileSwitchService } from './profile-switch.service';
import { AuthService } from '../../../core/services/auth.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { HistoryService } from '../../streaming/services/history.service';
import { PersonalAccountApiService } from './personal-account-api.service';
import { SecurityApiService } from './security-api.service';

describe('ProfileSwitchService history isolation', () => {
  let clearLocalCache: ReturnType<typeof vi.fn>;
  let clearAccountHistory: ReturnType<typeof vi.fn>;
  let clear: ReturnType<typeof vi.fn>;
  let stopPlayback: ReturnType<typeof vi.fn>;
  let svc: ProfileSwitchService;

  beforeEach(() => {
    clearLocalCache = vi.fn();
    clearAccountHistory = vi.fn();
    clear = vi.fn();
    stopPlayback = vi.fn();

    TestBed.configureTestingModule({
      providers: [
        ProfileSwitchService,
        provideRouter([{ path: 'login', children: [] }]),
        {
          provide: AuthService,
          useValue: {
            getUser: () => ({ id: 1 }),
            logout: vi.fn(),
            applySession: vi.fn(),
          },
        },
        { provide: MusicPlayerService, useValue: { stopPlayback } },
        {
          provide: OrganizationContextService,
          useValue: { clearOrganizationScopedState: vi.fn() },
        },
        {
          provide: HistoryService,
          useValue: { clearLocalCache, clearAccountHistory, clear },
        },
        { provide: PersonalAccountApiService, useValue: {} },
        { provide: SecurityApiService, useValue: {} },
      ],
    });

    svc = TestBed.inject(ProfileSwitchService);
    vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
  });

  it('clearPrivateClientState calls only clearLocalCache — never /listening-history/clear', () => {
    svc.clearPrivateClientState();
    expect(stopPlayback).toHaveBeenCalled();
    expect(clearLocalCache).toHaveBeenCalledTimes(1);
    expect(clearAccountHistory).not.toHaveBeenCalled();
    expect(clear).not.toHaveBeenCalled();
  });

  it('switchToLoginHint (logout path) never calls clearAccountHistory', () => {
    const auth = TestBed.inject(AuthService) as unknown as { logout: ReturnType<typeof vi.fn> };
    svc.switchToLoginHint('alice');
    expect(clearLocalCache).toHaveBeenCalled();
    expect(clearAccountHistory).not.toHaveBeenCalled();
    expect(clear).not.toHaveBeenCalled();
    expect(auth.logout).toHaveBeenCalled();
  });
});
