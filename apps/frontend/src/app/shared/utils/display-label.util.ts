/** Soften demo/seed markers in visible names (badge instead of inline text). */

const DEMO_SUFFIX =
  /\s*(?:\((?:Synthetic|Demo|Sintético|Demostración)\)|\[(?:SYNTHETIC|DEMO|SINTETICO)\])\s*$/i;
const DEMO_PREFIX = /^\s*\[(?:DEMO|SYNTHETIC|SINTETICO)\]\s*/i;

export interface SoftenedLabel {
  label: string;
  isDemo: boolean;
}

export function softenSyntheticLabel(raw: string | null | undefined): SoftenedLabel {
  let name = (raw ?? '').trim();
  if (!name) return { label: '', isDemo: false };
  let isDemo = false;
  if (DEMO_PREFIX.test(name)) {
    name = name.replace(DEMO_PREFIX, '').trim();
    isDemo = true;
  }
  if (DEMO_SUFFIX.test(name)) {
    name = name.replace(DEMO_SUFFIX, '').trim();
    isDemo = true;
  }
  return { label: name || (raw ?? '').trim(), isDemo };
}
