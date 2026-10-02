from time import sleep


class MockModelGateway:
    """Structured mock for the layout optimization black box.

    The gateway intentionally returns structured data only. Natural-language
    interpretation is owned by the backend business layer.
    """

    def evaluate_layout(self, scenario: dict) -> dict:
        sleep(0.35)
        return {
            "schemes": [
                {"id": "layout_A", "label": "方案 A · 近出口效率型", "note": "距离改善最大，改造范围较大", "score": 92},
                {"id": "layout_B", "label": "方案 B · 综合平衡型", "note": "效率、成本与风险保持平衡", "score": 88},
                {"id": "layout_C", "label": "方案 C · 低改造成本型", "note": "变更最少，效率改善有限", "score": 79},
            ],
            "kpis": [
                {
                    "metric": "拣选距离",
                    "baseline": "100.0 m/order",
                    "candidate": "85.2 m/order",
                    "delta": "-14.8%",
                    "entity": "整体拣选路径",
                    "type": "直接观测",
                    "confidence": "high",
                },
                {
                    "metric": "吞吐量",
                    "baseline": "1,000 order/day",
                    "candidate": "1,084 order/day",
                    "delta": "+8.4%",
                    "entity": "仓库整体",
                    "type": "直接观测",
                    "confidence": "high",
                },
                {
                    "metric": "通道 3 等待次数",
                    "baseline": "126 次",
                    "candidate": "78 次",
                    "delta": "-38.1%",
                    "entity": "通道 3",
                    "type": "统计归因",
                    "confidence": "medium",
                },
                {
                    "metric": "改造成本",
                    "baseline": "0 元",
                    "candidate": "176,000 元",
                    "delta": "低于预算 24,000 元",
                    "entity": "货位调整",
                    "type": "直接观测",
                    "confidence": "medium",
                },
            ],
            "insights": [
                {
                    "id": "insight_001",
                    "type": "statistical_attribution",
                    "title": "通道 3 等待显著下降",
                    "business_explanation": "高周转 SKU 被分配到靠近出库口的货位，减少了通道 3 的重复访问。",
                    "evidence_refs": ["evidence_003"],
                    "confidence": "medium",
                },
                {
                    "id": "insight_002",
                    "type": "tradeoff",
                    "title": "方案 B 不是距离最短，但更适合落地",
                    "business_explanation": "它在吞吐量、改造成本和实施风险之间保持平衡，满足吞吐量不低于当前布局的底线。",
                    "evidence_refs": ["evidence_001", "evidence_002", "evidence_004"],
                    "confidence": "high",
                },
            ],
            "recommendation": {
                "recommended_option": "layout_B",
                "alternative_options": ["layout_A", "layout_C"],
                "reasons": ["拣选距离下降 14.8%", "吞吐量提升 8.4%", "改造成本低于 20 万元预算"],
                "tradeoffs": ["方案 A 的距离改善更大，但需要更大范围调整", "方案 C 更省钱，但效率改善有限"],
                "risks": ["结果依赖历史平均拣选时间，建议补做旺季压力测试", "当前成本估算尚未计入临时培训成本"],
                "assumptions": ["订单范围为最近 30 天", "风险偏好为偏保守"],
                "approval_status": "pending",
            },
        }
