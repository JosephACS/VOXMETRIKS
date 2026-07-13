/** Demo local audio — WAV tones in src/assets/audio/ (tests / legacy only). */
export const DEMO_AUDIO_FILES = [
  '/assets/audio/demo-01.wav',
  '/assets/audio/demo-02.wav',
  '/assets/audio/demo-03.wav',
  '/assets/audio/demo-04.wav',
  '/assets/audio/demo-05.wav',
  '/assets/audio/demo-06.wav',
  '/assets/audio/demo-07.wav',
  '/assets/audio/demo-08.wav',
];

/** @deprecated Do not attach to PlayableTrack for real playback. */
export function demoAudioUrlForTrack(trackId: number): string {
  const idx = Math.abs(trackId) % DEMO_AUDIO_FILES.length;
  return DEMO_AUDIO_FILES[idx];
}

/** True when URL is a generic catalog tone, not a track-specific preview. */
export function isGenericDemoAudioUrl(url?: string | null): boolean {
  if (!url) return false;
  return /\/assets\/audio\/demo-\d+\.wav(?:\?|$)/i.test(url);
}
