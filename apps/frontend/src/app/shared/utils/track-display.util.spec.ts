import { displayTrackTitle } from './track-display.util';

describe('track display', () => {
  it('removes imported video labels while preserving meaningful editions', () => {
    expect(displayTrackTitle('Never Gonna Give You Up (Official Animated Video)'))
      .toBe('Never Gonna Give You Up');
    expect(displayTrackTitle('Never Gonna Give You Up (Official Video) (4K Remaster)'))
      .toBe('Never Gonna Give You Up (4K Remaster)');
  });

  it('keeps ordinary song titles untouched', () => {
    expect(displayTrackTitle('Video Games')).toBe('Video Games');
  });
});
