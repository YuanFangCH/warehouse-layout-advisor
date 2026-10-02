import { describe, expect, it } from 'vitest';

import { DURATIONS, STAGGER_DELAY } from '../src/design/motion';

describe('motion tokens', () => {
  it('keeps interface motion short and interruptible', () => {
    expect(Object.values(DURATIONS).every((duration) => duration <= 0.3)).toBe(true);
  });

  it('uses a single stagger cadence for page entrances', () => {
    expect(STAGGER_DELAY).toBe(0.04);
  });
});
