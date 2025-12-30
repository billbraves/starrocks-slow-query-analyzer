---
name: starrocks-slow-query-analysis
description: StarRocks 慢 SQL 分析与优化技能 - 自动识别、诊断和优化慢查询，提供性能优化建议
parameters:
  type: object
  properties:
    time_range:
      type: integer
      description: 分析时间范围（小时），默认 24 小时
      default: 24
    threshold:
      type: number
      description: 慢 SQL 阈值（秒），默认 1 秒
      default: 1.0
    output_format:
      type: string
      description: 输出格式：html、markdown、json
      default: html
      enum: [html, markdown, json]
    detailed_analysis:
      type: boolean
      description: 是否执行详细分析（包括执行计划分析），默认 true
      default: true
  required: []
---

# StarRocks 慢 SQL 分析技能

此技能用于分析 StarRocks 数据库中的慢 SQL，识别性能问题并提供优化建议。

## 功能特性

- 自动获取慢 SQL 列表
- 查询性能分析（执行时间、扫描行数、内存使用等）
- SQL 解析和模式识别
- 执行计划分析
- 智能优化建议生成
- 多格式报告输出（HTML/Markdown/JSON）

## 使用示例

### 基础分析
```bash
# 分析过去 24 小时的慢 SQL（默认阈值 1 秒）
请帮我分析 StarRocks 过去 24 小时的慢 SQL

# 自定义时间范围和阈值
请帮我分析 StarRocks 过去 6 小时的慢 SQL，阈值设为 0.5 秒
```

### 详细分析
```bash
# 包含执行计划的详细分析
请详细分析 StarRocks 的慢 SQL，包括执行计划

# 分析特定表相关的慢 SQL
请帮我分析与表 orders、users 相关的慢 SQL
```

### 优化建议
```bash
# 获取优化建议
请分析慢 SQL 并提供优化建议

# 诊断特定 SQL
请帮我诊断这个 SQL 的性能问题：[粘贴 SQL]
```

## 报告生成

分析完成后会自动生成报告文件，包括：

- 慢 SQL 排行榜
- 性能指标统计
- 问题分类汇总
- 优化建议列表

报告默认保存在 `./reports` 目录下。

## 技术实现

核心模块：
- `starrocks_connector.py`: 数据库连接和查询
- `slow_query_collector.py`: 慢 SQL 收集
- `query_analyzer.py`: SQL 分析和诊断
- `optimization_suggester.py`: 优化建议生成
- `report_generator.py`: 报告生成

