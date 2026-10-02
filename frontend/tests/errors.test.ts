import { describe, expect, it } from 'vitest';

import { errorMessage } from '../src/utils/errors';

describe('errorMessage', () => {
  it('maps known backend codes to user-facing messages', () => {
    expect(errorMessage('SCENARIO_VERSION_CONFLICT')).toContain('刷新');
    expect(errorMessage('MODEL_SERVICE_UNAVAILABLE')).toContain('不可用');
    expect(errorMessage('DECISION_ALREADY_APPROVED')).toContain('确认');
  });

  it('falls back to a generic message for unknown codes', () => {
    expect(errorMessage('SOMETHING_ELSE')).toBe('请求失败，请稍后重试');
  });
});
