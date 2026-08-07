import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AuthResponse } from '../../../shared/models/api.models';

export interface PinStatus {
  enabled: boolean;
  require_on_select: boolean;
  lock_on_switch: boolean;
  locked: boolean;
  locked_until?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PinEnableBody {
  password: string;
  pin: string;
  pin_confirm: string;
  require_on_select?: boolean;
  lock_on_switch?: boolean;
}

export interface PinPrefsBody {
  require_on_select?: boolean;
  lock_on_switch?: boolean;
}

export interface PasswordChangeBody {
  current_password: string;
  new_password: string;
  confirm_password: string;
  revoke_other_sessions?: boolean;
}

export interface DeviceAuthorizeBody {
  password: string;
  device_label?: string;
  browser?: string;
  os_name?: string;
}

export interface TrustedDevice {
  id: number;
  device_label?: string | null;
  browser?: string | null;
  os_name?: string | null;
  status: string;
  authorized_at?: string | null;
  expires_at?: string | null;
  last_seen_at?: string | null;
}

export interface SecurityActivityItem {
  action: string;
  summary: string;
  created_at?: string | null;
}

export interface PinUnlockSwitchBody {
  target_user_id: number;
  pin: string;
  device_token: string;
}

export type PinUnlockSwitchResponse = { ok: true } | AuthResponse;

export interface SecurityErrorDetail {
  code?: string;
  message?: string;
}

@Injectable({ providedIn: 'root' })
export class SecurityApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/security`;

  getPinStatus(): Observable<PinStatus> {
    return this.http.get<PinStatus>(`${this.base}/pin`);
  }

  enablePin(body: PinEnableBody): Observable<PinStatus> {
    return this.http.post<PinStatus>(`${this.base}/pin/enable`, body);
  }

  changePin(body: PinEnableBody): Observable<PinStatus> {
    return this.http.post<PinStatus>(`${this.base}/pin/change`, body);
  }

  disablePin(password: string): Observable<PinStatus> {
    return this.http.post<PinStatus>(`${this.base}/pin/disable`, { password });
  }

  resetPin(body: PinEnableBody): Observable<PinStatus> {
    return this.http.post<PinStatus>(`${this.base}/pin/reset`, body);
  }

  verifyPin(pin: string, deviceToken?: string | null): Observable<{ ok: true }> {
    return this.http.post<{ ok: true }>(`${this.base}/pin/verify`, {
      pin,
      device_token: deviceToken ?? undefined,
    });
  }

  updatePinPreferences(body: PinPrefsBody): Observable<PinStatus> {
    return this.http.patch<PinStatus>(`${this.base}/pin/preferences`, body);
  }

  unlockPinSwitch(body: PinUnlockSwitchBody): Observable<PinUnlockSwitchResponse> {
    return this.http.post<PinUnlockSwitchResponse>(`${this.base}/pin/unlock-switch`, body);
  }

  listDevices(): Observable<{ items: TrustedDevice[] }> {
    return this.http.get<{ items: TrustedDevice[] }>(`${this.base}/devices`);
  }

  authorizeDevice(body: DeviceAuthorizeBody): Observable<{
    device_id: number;
    device_token: string;
    expires_at?: string;
    allow_pin_unlock?: boolean;
  }> {
    return this.http.post<{
      device_id: number;
      device_token: string;
      expires_at?: string;
      allow_pin_unlock?: boolean;
    }>(`${this.base}/devices/authorize`, body);
  }

  revokeDevice(deviceId: number): Observable<{ ok?: boolean }> {
    return this.http.post<{ ok?: boolean }>(`${this.base}/devices/${deviceId}/revoke`, {});
  }

  revokeOtherDevices(keepDeviceToken?: string | null): Observable<{ ok?: boolean }> {
    return this.http.post<{ ok?: boolean }>(`${this.base}/devices/revoke-others`, {
      keep_device_token: keepDeviceToken ?? undefined,
    });
  }

  revokeOtherSessions(): Observable<{ ok?: boolean }> {
    return this.http.post<{ ok?: boolean }>(`${this.base}/sessions/revoke-others`, {});
  }

  changePassword(body: PasswordChangeBody): Observable<{ ok?: boolean }> {
    return this.http.post<{ ok?: boolean }>(`${this.base}/password/change`, body);
  }

  getActivity(): Observable<{ items: SecurityActivityItem[] }> {
    return this.http.get<{ items: SecurityActivityItem[] }>(`${this.base}/activity`);
  }

  /** Extract backend security error code from HttpErrorResponse-shaped objects. */
  static errorCode(err: unknown): string | null {
    const e = err as { error?: { detail?: SecurityErrorDetail | string }; status?: number };
    const detail = e?.error?.detail;
    if (typeof detail === 'object' && detail?.code) return detail.code;
    if (e?.status === 403) return 'forbidden';
    return null;
  }

  static errorMessage(err: unknown): string | null {
    const e = err as { error?: { detail?: SecurityErrorDetail | string } };
    const detail = e?.error?.detail;
    if (typeof detail === 'object' && detail?.message) return detail.message;
    if (typeof detail === 'string') return detail;
    return null;
  }
}
