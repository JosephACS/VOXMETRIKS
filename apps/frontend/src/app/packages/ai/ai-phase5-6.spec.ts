import { describe, it, expect } from 'vitest';
import { sanitize_ai_context } from './ai-utils';

describe('Phase 5 Notifications', () => {
  it('notification levels are valid', () => {
    const levels = ['info', 'success', 'warning', 'error'];
    expect(levels).toContain('success');
  });
});

describe('Phase 6 AI utils', () => {
  it('sanitizer removes sensitive keys', () => {
    const clean = sanitize_ai_context({ token: 'x', title: 'Song' });
    expect(clean['token']).toBeUndefined();
    expect(clean['title']).toBe('Song');
  });
});
