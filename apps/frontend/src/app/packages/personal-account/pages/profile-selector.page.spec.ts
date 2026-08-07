import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { environment } from '../../../../environments/environment';
import { ProfileSelectorPage } from './profile-selector.page';
import { ProfileSwitchService } from '../services/profile-switch.service';
import { SecurityApiService } from '../services/security-api.service';
import { TrustedDeviceService } from '../services/trusted-device.service';
import { AuthService } from '../../../core/services/auth.service';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { HistoryService } from '../../streaming/services/history.service';
import { FavoritesService } from '../../streaming/services/favorites.service';

describe('ProfileSelectorPage', () => {
  let fixture: ComponentFixture<ProfileSelectorPage>;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileSelectorPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ProfileSwitchService,
        {
          provide: AuthService,
          useValue: {
            getUser: () => ({ id: 1, username: 'household.owner' }),
            logout: vi.fn(),
            isAuthenticated: () => true,
            state: () => ({ user: { id: 1 }, token: 't' }),
          },
        },
        { provide: MusicPlayerService, useValue: { stopPlayback: vi.fn() } },
        {
          provide: OrganizationContextService,
          useValue: { clearOrganizationScopedState: vi.fn() },
        },
        { provide: HistoryService, useValue: { reload: vi.fn(), clear: vi.fn() } },
        { provide: FavoritesService, useValue: { refreshIds: vi.fn() } },
        {
          provide: SecurityApiService,
          useValue: {
            getPinStatus: vi.fn(),
            verifyPin: vi.fn(),
            unlockPinSwitch: vi.fn(),
          },
        },
        {
          provide: TrustedDeviceService,
          useValue: {
            getToken: vi.fn(() => null),
            setToken: vi.fn(),
            clearToken: vi.fn(),
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ProfileSelectorPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('renders Who is listening cards without emails or ids in the UI', async () => {
    fixture.detectChanges();
    http.expectOne(`${base}/personal/household/profiles`).flush({
      show_selector: true,
      plan_active: true,
      profiles: [
        {
          user_id: 1,
          display_name: 'Joseph',
          initials: 'JO',
          avatar_hue: 40,
          role: 'owner',
          is_me: true,
        },
        {
          user_id: 2,
          display_name: 'María',
          initials: 'MA',
          avatar_hue: 120,
          role: 'member',
          is_me: false,
        },
      ],
    });
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent as string;
    expect(text).toMatch(/Quién va a escuchar|Who is listening/i);
    expect(text).toContain('Joseph');
    expect(text).toContain('María');
    expect(text).not.toContain('@');
    expect(text).not.toContain('user_id');
    expect(fixture.nativeElement.querySelector('[data-testid="who-listening-page"]')).toBeTruthy();
  });

  it('opens privacy modal when selecting another member', async () => {
    fixture.detectChanges();
    http.expectOne(`${base}/personal/household/profiles`).flush({
      show_selector: true,
      plan_active: true,
      profiles: [
        { user_id: 1, display_name: 'Joseph', initials: 'JO', avatar_hue: 10, role: 'owner', is_me: true },
        { user_id: 2, display_name: 'María', initials: 'MA', avatar_hue: 90, role: 'member', is_me: false },
      ],
    });
    await fixture.whenStable();
    fixture.detectChanges();
    const cards = fixture.nativeElement.querySelectorAll('.wl-card') as NodeListOf<HTMLButtonElement>;
    cards[1].click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toMatch(/Cambiar a este perfil|Switch to this profile/i);
  });
});

describe('ProfileSwitchService', () => {
  it('prompts when shared household and no remember/session skip', () => {
    const svc = TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ProfileSwitchService,
        { provide: AuthService, useValue: { getUser: () => ({ id: 7 }), logout: vi.fn() } },
        { provide: MusicPlayerService, useValue: { stopPlayback: vi.fn() } },
        {
          provide: OrganizationContextService,
          useValue: { clearOrganizationScopedState: vi.fn() },
        },
      ],
    }).inject(ProfileSwitchService);
    localStorage.removeItem('voxmetriks_ask_who_listening');
    localStorage.removeItem('voxmetriks_remember_profile_7');
    sessionStorage.removeItem('voxmetriks_profile_session_selected');
    expect(svc.shouldPromptSelector(2, 7)).toBe(true);
    svc.setRememberProfile(true, 7);
    expect(svc.shouldPromptSelector(2, 7)).toBe(false);
    svc.setRememberProfile(false, 7);
    svc.markSessionSelected(7);
    expect(svc.shouldPromptSelector(2, 7)).toBe(false);
    expect(svc.shouldPromptSelector(1, 7)).toBe(false);
  });
});
