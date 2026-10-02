const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: '请求字段不完整，请检查后重试',
  MISSING_DATA: '缺少必要数据，请刷新后重试',
  SCENARIO_VERSION_CONFLICT: '场景已产生新版本，已为你刷新当前场景',
  MODEL_SERVICE_UNAVAILABLE: '模型服务暂不可用',
  EVALUATION_TIMEOUT: '评估超时，请重新发起',
  NO_FEASIBLE_SCENARIO: '没有满足条件的方案',
  RECOMMENDATION_UNCERTAIN: '当前推荐置信度不足',
  DECISION_ALREADY_APPROVED: '该方案已经确认',
  PENDING_CLARIFICATIONS: '仍有待确认问题',
  SCENARIO_NOT_FOUND: '场景不存在',
  PROJECT_NOT_FOUND: '项目不存在',
  EVALUATION_NOT_FOUND: '评估任务不存在',
  QUESTION_NOT_FOUND: '澄清问题不存在',
  QUESTION_ALREADY_ANSWERED: '该问题已经回答',
  SCENARIO_NOT_READY: '场景尚未就绪',
  RECOMMENDATION_NOT_READY: '推荐结果尚未生成',
};

export function errorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? '请求失败，请稍后重试';
}
