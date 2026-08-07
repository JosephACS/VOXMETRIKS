import { Injectable } from '@angular/core';

const TOKEN_PREFIX = 'voxmetriks_device_token_';

@Injectable({ providedIn: 'root' })
export class TrustedDeviceService {
  private key(userId: number): string {
    return `${TOKEN_PREFIX}${userId}`;
  }

  getToken(userId: number): string | null {
    try {
      return localStorage.getItem(this.key(userId));
    } catch {
      return null;
    }
  }

  setToken(userId: number, token: string): void {
    try {
      localStorage.setItem(this.key(userId), token);
    } catch {
      /* ignore quota / private mode */
    }
  }

  clearToken(userId: number): void {
    try {
      localStorage.removeItem(this.key(userId));
    } catch {
      /* ignore */
    }
  }

  detectBrowser(): string {
    const ua = navigator.userAgent;
    if (/Edg\//i.test(ua)) return 'Edge';
    if (/OPR\//i.test(ua) || /Opera/i.test(ua)) return 'Opera';
    if (/Chrome\//i.test(ua) && !/Edg\//i.test(ua)) return 'Chrome';
    if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) return 'Safari';
    if (/Firefox/i.test(ua)) return 'Firefox';
    return 'Browser';
  }

  detectOs(): string {
    const ua = navigator.userAgent;
    if (/Windows NT/i.test(ua)) return 'Windows';
    if (/Mac OS X/i.test(ua) && !/iPhone|iPad/i.test(ua)) return 'macOS';
    if (/Android/i.test(ua)) return 'Android';
    if (/iPhone|iPad|iPod/i.test(ua)) return 'iOS';
    if (/Linux/i.test(ua)) return 'Linux';
    return 'Unknown';
  }
}
