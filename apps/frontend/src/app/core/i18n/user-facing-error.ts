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
  const rawDetail = e.error?.detail;
  let detail = '';
  if (typeof rawDetail === 'string') {
    detail = rawDetail;
  } else if (rawDetail && typeof rawDetail === 'object') {
    const msg = (rawDetail as { message?: unknown }).message;
    if (typeof msg === 'string' && msg.trim()) detail = msg.trim();
  }
  if (!detail && typeof e.error?.message === 'string') detail = e.error.message;
  if (!detail && typeof e.message === 'string') detail = e.message;

  if (detail && !isTechnicalErrorMessage(detail) && detail.length <= 180) {
    return detail;
  }
  return i18n.t(httpErrorKey(status));
}
