import { I18nService } from '../services/i18n.service';
import { httpErrorKey, isTechnicalErrorMessage } from '../i18n/http-error-keys';

interface ErrLike {
  status?: number;
  message?: string;
  error?: { detail?: unknown; message?: string };
}

/** Map API failures to translated user messages (no technical dumps). */
export function userFacingHttpError(i18n: I18nService, err: unknown): string {
  const e = (err ?? {}) as ErrLike;
  const status = typeof e.status === 'number' ? e.status : undefined;
  const detail =
    (typeof e.error?.detail === 'string' && e.error.detail) ||
    (typeof e.error?.message === 'string' && e.error.message) ||
    (typeof e.message === 'string' && e.message) ||
    '';

  if (detail && !isTechnicalErrorMessage(detail) && detail.length <= 180 && !status) {
    return detail;
  }
  return i18n.t(httpErrorKey(status));
}
