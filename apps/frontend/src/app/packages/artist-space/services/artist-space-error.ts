import { I18nService } from '../../../core/services/i18n.service';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';

/** Stable backend codes (051 contract) mapped to translated copy. */
const CODE_KEYS: Record<string, string> = {
  artist_not_found: 'artistSpace.error.artistNotFound',
  artist_membership_required: 'artistSpace.error.membershipRequired',
  artist_permission_denied: 'artistSpace.error.permissionDenied',
  artist_request_conflict: 'artistSpace.error.requestConflict',
  artist_request_invalid_state: 'artistSpace.error.requestInvalidState',
  artist_evidence_required: 'artistSpace.error.evidenceRequired',
  artist_workspace_provision_failed: 'artistSpace.error.workspaceProvisionFailed',
  release_artist_mismatch: 'artistSpace.error.releaseArtistMismatch',
  release_invalid_state: 'artistSpace.error.releaseInvalidState',
  release_incomplete: 'artistSpace.error.releaseIncomplete',
  self_review_forbidden: 'artistSpace.error.selfReviewForbidden',
  permission_denied: 'artistSpace.error.permissionDenied',
};

interface DetailLike {
  code?: unknown;
  message?: unknown;
}

/**
 * Translate an artist-journey API failure. Falls back to the shared HTTP mapper
 * so no caller ever renders a raw exception or silently swallows the error.
 */
export function artistJourneyError(i18n: I18nService, err: unknown): string {
  const detail = (err as { error?: { detail?: unknown } } | null)?.error?.detail;
  if (detail && typeof detail === 'object') {
    const { code, message } = detail as DetailLike;
    if (typeof code === 'string' && CODE_KEYS[code]) {
      return i18n.t(CODE_KEYS[code]);
    }
    if (typeof message === 'string' && message.trim()) {
      const msg = message.trim();
      // Backend validate_ready / submit often returns validation_error with blockers in message.
      if (/missing_cover|missing_audio|not ready|Submission not ready/i.test(msg)) {
        return i18n.t('artistSpace.error.releaseIncomplete');
      }
      return msg;
    }
  }
  if (typeof detail === 'string' && /missing_cover|missing_audio|not ready/i.test(detail)) {
    return i18n.t('artistSpace.error.releaseIncomplete');
  }
  return userFacingHttpError(i18n, err);
}
