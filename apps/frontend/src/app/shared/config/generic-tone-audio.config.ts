/** Generic local tone WAV files in src/assets/audio/ (blocklist / legacy URLs only). */
export const GENERIC_TONE_AUDIO_FILES = [
  '/assets/audio/demo-01.wav',
  '/assets/audio/demo-02.wav',
  '/assets/audio/demo-03.wav',
  '/assets/audio/demo-04.wav',
  '/assets/audio/demo-05.wav',
  '/assets/audio/demo-06.wav',
  '/assets/audio/demo-07.wav',
  '/assets/audio/demo-08.wav',
];

/** True when URL is a generic catalog tone, not a track-specific preview. */
export function isGenericToneAudioUrl(url?: string | null): boolean {
  if (!url) return false;
  return /\/assets\/audio\/demo-\d+\.wav(?:\?|$)/i.test(url);
}
