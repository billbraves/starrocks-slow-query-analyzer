#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器
生成慢 SQL 分析报告（HTML、Markdown、JSON 格式）
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from jinja2 import Template
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化报告生成器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.report_dir = self.config.get('report_dir', './reports')
        self.report_format = self.config.get('report_format', 'html')
        
        # 创建报告目录
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_report(
        self,
        slow_queries: List,
        statistics: Dict[str, Any],
        problems_by_query: Dict[str, List],
        suggestions_by_query: Dict[str, List],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成分析报告
        
        Args:
            slow_queries: 慢查询列表
            statistics: 统计信息
            problems_by_query: 按查询ID分组的问题
            suggestions_by_query: 按查询ID分组的建议
            metadata: 元数据（时间范围等）
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.report_format == 'html':
            return self._generate_html_report(
                slow_queries, statistics, problems_by_query, 
                suggestions_by_query, metadata, timestamp
            )
        elif self.report_format == 'markdown':
            return self._generate_markdown_report(
                slow_queries, statistics, problems_by_query,
                suggestions_by_query, metadata, timestamp
            )
        elif self.report_format == 'json':
            return self._generate_json_report(
                slow_queries, statistics, problems_by_query,
                suggestions_by_query, metadata, timestamp
            )
        else:
            raise ValueError(f"不支持的报告格式: {self.report_format}")
    
    def _generate_html_report(
        self,
        slow_queries: List,
        statistics: Dict[str, Any],
        problems_by_query: Dict[str, List],
        suggestions_by_query: Dict[str, List],
        metadata: Optional[Dict[str, Any]],
        timestamp: str
    ) -> str:
        """生成 HTML 报告"""
        
        html_template = Template('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StarRocks 慢 SQL 分析报告</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }
        
        h3 {
            color: #555;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        
        .metadata {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        
        .metadata p {
            margin: 5px 0;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-card h3 {
            color: white;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .severity-critical { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }
        .severity-high { background: linear-gradient(135deg, #f39c12 0%, #d35400 100%); }
        .severity-medium { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
        .severity-low { background: linear-gradient(135deg, #27ae60 0%, #229954 100%); }
        
        .query-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .query-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .query-id {
            font-family: monospace;
            color: #666;
            font-size: 0.9em;
        }
        
        .severity-badge {
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }
        
        .severity-critical { background: #e74c3c; }
        .severity-high { background: #f39c12; }
        .severity-medium { background: #3498db; }
        .severity-low { background: #27ae60; }
        
        .sql-box {
            background: #282c34;
            color: #abb2bf;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.9em;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .metric {
            background: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.85em;
        }
        
        .metric-value {
            color: #2c3e50;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .problem-list, .suggestion-list {
            margin-top: 15px;
        }
        
        .problem-item {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 3px;
        }
        
        .problem-item.high {
            background: #f8d7da;
            border-left-color: #dc3545;
        }
        
        .suggestion-item {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 3px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #3498db;
            color: white;
            font-weight: bold;
        }
        
        tr:hover {
            background: #f5f5f5;
        }
        
        .priority-high {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .priority-medium {
            color: #f39c12;
            font-weight: bold;
        }
        
        .priority-low {
            color: #27ae60;
            font-weight: bold;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐘 StarRocks 慢 SQL 分析报告</h1>
        
        <div class="metadata">
            <p><strong>报告生成时间:</strong> {{ report_time }}</p>
            <p><strong>分析时间范围:</strong> {{ metadata.time_range }} 小时</p>
            <p><strong>慢查询阈值:</strong> {{ metadata.threshold }} 秒</p>
            {% if metadata.database %}
            <p><strong>分析数据库:</strong> {{ metadata.database }}</p>
            {% endif %}
        </div>
        
        <h2>📊 统计概览</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <h3>总慢查询数</h3>
                <div class="value">{{ statistics.total_queries }}</div>
            </div>
            <div class="stat-card">
                <h3>平均执行时间</h3>
                <div class="value">{{ "%.2f"|format(statistics.avg_execution_time) }}s</div>
            </div>
            <div class="stat-card">
                <h3>最大执行时间</h3>
                <div class="value">{{ "%.2f"|format(statistics.max_execution_time) }}s</div>
            </div>
            <div class="stat-card">
                <h3>总扫描行数</h3>
                <div class="value">{{ "{:,}".format(statistics.total_scan_rows) }}</div>
            </div>
        </div>
        
        <h2>📈 严重程度分布</h2>
        <div class="stats-grid">
            {% for severity, count in statistics.severity_distribution.items() %}
            <div class="stat-card severity-{{ severity.lower() }}">
                <h3>{{ severity }}</h3>
                <div class="value">{{ count }}</div>
            </div>
            {% endfor %}
        </div>
        
        <h2>🔍 慢查询详情</h2>
        {% for query in slow_queries[:20] %}
        <div class="query-card">
            <div class="query-header">
                <div>
                    <span class="query-id">Query ID: {{ query.query_id }}</span>
                    <br>
                    <small>数据库: {{ query.database }} | 用户: {{ query.user }}</small>
                </div>
                <span class="severity-badge severity-{{ query.severity.lower() }}">
                    {{ query.severity }}
                </span>
            </div>
            
            <div class="sql-box">{{ query.query_text }}</div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">执行时间</div>
                    <div class="metric-value">{{ "%.2f"|format(query.execution_time) }}s</div>
                </div>
                <div class="metric">
                    <div class="metric-label">扫描行数</div>
                    <div class="metric-value">{{ query.scan_rows_formatted }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">扫描字节数</div>
                    <div class="metric-value">{{ query.scan_bytes_formatted }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">内存使用</div>
                    <div class="metric-value">{{ "{:.2f}".format(query.memory_used / 1048576) }} MB</div>
                </div>
            </div>
            
            {% if query.query_id in problems_by_query %}
            <h3>⚠️ 发现的问题</h3>
            <div class="problem-list">
                {% for problem in problems_by_query[query.query_id] %}
                <div class="problem-item {{ 'high' if problem.severity in ['CRITICAL', 'HIGH'] else '' }}">
                    <strong>{{ problem.problem_type.value }}</strong> 
                    <span class="priority-{{ problem.severity.lower() }}">[{{ problem.severity }}]</span>
                    <p>{{ problem.description }}</p>
                    <p><strong>建议:</strong> {{ problem.suggestion }}</p>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if query.query_id in suggestions_by_query %}
            <h3>💡 优化建议</h3>
            <div class="suggestion-list">
                {% for suggestion in suggestions_by_query[query.query_id] %}
                <div class="suggestion-item">
                    <strong>{{ suggestion.title }}</strong> 
                    <span class="priority-{{ suggestion.priority.lower() }}">[{{ suggestion.priority }}]</span>
                    <p>{{ suggestion.description }}</p>
                    {% if suggestion.suggested_sql %}
                    <div class="sql-box">{{ suggestion.suggested_sql }}</div>
                    {% endif %}
                    {% if suggestion.estimated_improvement %}
                    <p><strong>预期提升:</strong> {{ suggestion.estimated_improvement }}</p>
                    {% endif %}
                    {% if suggestion.implementation_notes %}
                    <p><strong>实施说明:</strong> {{ suggestion.implementation_notes }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
        
        <h2>📋 优化建议汇总</h2>
        <table>
            <thead>
                <tr>
                    <th>优先级</th>
                    <th>类别</th>
                    <th>标题</th>
                    <th>预期提升</th>
                </tr>
            </thead>
            <tbody>
                {% for query_id, suggestions in suggestions_by_query.items() %}
                {% for suggestion in suggestions %}
                <tr>
                    <td class="priority-{{ suggestion.priority.lower() }}">{{ suggestion.priority }}</td>
                    <td>{{ suggestion.category }}</td>
                    <td>{{ suggestion.title }}</td>
                    <td>{{ suggestion.estimated_improvement or '未知' }}</td>
                </tr>
                {% endfor %}
                {% endfor %}
            </tbody>
        </table>
        
        <div class="footer">
            <p>📅 生成于: {{ report_time }} | 🔧 StarRocks 慢 SQL 分析工具</p>
        </div>
    </div>
</body>
</html>
        ''')
        
        html_content = html_template.render(
            report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            metadata=metadata or {},
            statistics=statistics,
            slow_queries=slow_queries,
            problems_by_query=problems_by_query,
            suggestions_by_query=suggestions_by_query
        )
        
        filename = os.path.join(self.report_dir, f'slow_query_report_{timestamp}.html')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML 报告已生成: {filename}")
        return filename
    
    def _generate_markdown_report(
        self,
        slow_queries: List,
        statistics: Dict[str, Any],
        problems_by_query: Dict[str, List],
        suggestions_by_query: Dict[str, List],
        metadata: Optional[Dict[str, Any]],
        timestamp: str
    ) -> str:
        """生成 Markdown 报告"""
        
        md_lines = [
            "# 🐘 StarRocks 慢 SQL 分析报告\n",
            "## 📋 报告元数据",
            f"- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **分析时间范围**: {metadata.get('time_range', 24)} 小时",
            f"- **慢查询阈值**: {metadata.get('threshold', 1.0)} 秒",
        ]
        
        if metadata and metadata.get('database'):
            md_lines.append(f"- **分析数据库**: {metadata['database']}")
        
        md_lines.extend([
            "",
            "## 📊 统计概览",
            f"- **总慢查询数**: {statistics['total_queries']}",
            f"- **平均执行时间**: {statistics['avg_execution_time']:.2f}s",
            f"- **最大执行时间**: {statistics['max_execution_time']:.2f}s",
            f"- **总扫描行数**: {statistics['total_scan_rows']:,}",
            "",
            "## 📈 严重程度分布",
        ])
        
        for severity, count in statistics['severity_distribution'].items():
            md_lines.append(f"- **{severity}**: {count}")
        
        md_lines.extend([
            "",
            "## 🔍 慢查询详情",
        ])
        
        for i, query in enumerate(slow_queries[:20], 1):
            md_lines.extend([
                f"\n### {i}. Query ID: `{query.query_id}`",
                f"**数据库**: {query.database} | **用户**: {query.user} | **严重程度**: {query.severity}",
                "",
                "#### SQL",
                f"```sql\n{query.query_text}\n```",
                "",
                "#### 性能指标",
                f"- 执行时间: {query.execution_time:.2f}s",
                f"- 扫描行数: {query.scan_rows_formatted}",
                f"- 扫描字节数: {query.scan_bytes_formatted}",
                f"- 内存使用: {query.memory_used / 1048576:.2f} MB",
            ])
            
            if query.query_id in problems_by_query:
                md_lines.append("\n#### ⚠️ 发现的问题")
                for problem in problems_by_query[query.query_id]:
                    md_lines.extend([
                        f"- **{problem.problem_type.value}** [{problem.severity}]",
                        f"  - {problem.description}",
                        f"  - 建议: {problem.suggestion}",
                    ])
            
            if query.query_id in suggestions_by_query:
                md_lines.append("\n#### 💡 优化建议")
                for suggestion in suggestions_by_query[query.query_id]:
                    md_lines.extend([
                        f"- **{suggestion.title}** [{suggestion.priority}]",
                        f"  - {suggestion.description}",
                    ])
                    if suggestion.suggested_sql:
                        md_lines.append(f"  ```sql\n  {suggestion.suggested_sql}\n  ```")
                    if suggestion.estimated_improvement:
                        md_lines.append(f"  - 预期提升: {suggestion.estimated_improvement}")
                    if suggestion.implementation_notes:
                        md_lines.append(f"  - 实施说明: {suggestion.implementation_notes}")
        
        md_lines.extend([
            "\n## 📋 优化建议汇总",
            "\n| 优先级 | 类别 | 标题 | 预期提升 |",
            "|--------|------|------|----------|",
        ])
        
        for query_id, suggestions in suggestions_by_query.items():
            for suggestion in suggestions:
                md_lines.append(
                    f"| {suggestion.priority} | {suggestion.category} | {suggestion.title} | {suggestion.estimated_improvement or '未知'} |"
                )
        
        md_lines.extend([
            "",
            "---",
            f"\n📅 生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🔧 StarRocks 慢 SQL 分析工具\n"
        ])
        
        md_content = '\n'.join(md_lines)
        filename = os.path.join(self.report_dir, f'slow_query_report_{timestamp}.md')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown 报告已生成: {filename}")
        return filename
    
    def _generate_json_report(
        self,
        slow_queries: List,
        statistics: Dict[str, Any],
        problems_by_query: Dict[str, List],
        suggestions_by_query: Dict[str, List],
        metadata: Optional[Dict[str, Any]],
        timestamp: str
    ) -> str:
        """生成 JSON 报告"""
        
        report_data = {
            "metadata": {
                "report_time": datetime.now().isoformat(),
                "time_range_hours": metadata.get('time_range', 24) if metadata else 24,
                "threshold_seconds": metadata.get('threshold', 1.0) if metadata else 1.0,
                "database": metadata.get('database') if metadata else None,
            },
            "statistics": statistics,
            "slow_queries": [],
        }
        
        for query in slow_queries:
            query_data = {
                "query_id": query.query_id,
                "query_text": query.query_text,
                "database": query.database,
                "user": query.user,
                "execution_time": query.execution_time,
                "scan_rows": query.scan_rows,
                "scan_bytes": query.scan_bytes,
                "memory_used": query.memory_used,
                "cpu_time": query.cpu_time,
                "start_time": query.start_time.isoformat(),
                "end_time": query.end_time.isoformat(),
                "severity": query.severity,
                "problems": [],
                "suggestions": []
            }
            
            if query.query_id in problems_by_query:
                for problem in problems_by_query[query.query_id]:
                    query_data["problems"].append({
                        "type": problem.problem_type.value,
                        "severity": problem.severity,
                        "description": problem.description,
                        "suggestion": problem.suggestion,
                        "evidence": problem.evidence
                    })
            
            if query.query_id in suggestions_by_query:
                for suggestion in suggestions_by_query[query.query_id]:
                    query_data["suggestions"].append({
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "priority": suggestion.priority,
                        "category": suggestion.category,
                        "suggested_sql": suggestion.suggested_sql,
                        "estimated_improvement": suggestion.estimated_improvement,
                        "implementation_notes": suggestion.implementation_notes
                    })
            
            report_data["slow_queries"].append(query_data)
        
        filename = os.path.join(self.report_dir, f'slow_query_report_{timestamp}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON 报告已生成: {filename}")
        return filename

