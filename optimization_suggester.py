#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化建议生成器
生成针对性的 SQL 优化建议
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    title: str
    description: str
    priority: str  # HIGH, MEDIUM, LOW
    category: str  # INDEX, QUERY, SCHEMA, CONFIG
    original_sql: str
    suggested_sql: Optional[str] = None
    estimated_improvement: Optional[str] = None
    implementation_notes: Optional[str] = None


class OptimizationSuggester:
    """优化建议生成器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化建议生成器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
    
    def generate_suggestions(
        self,
        query_info,
        problems: List,
        table_schema: Optional[Dict] = None
    ) -> List[OptimizationSuggestion]:
        """
        生成优化建议
        
        Args:
            query_info: 查询信息
            problems: 问题列表
            table_schema: 表结构信息
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        for problem in problems:
            suggestion = self._generate_suggestion_for_problem(query_info, problem, table_schema)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_suggestion_for_problem(
        self,
        query_info,
        problem,
        table_schema: Optional[Dict]
    ) -> Optional[OptimizationSuggestion]:
        """
        为单个问题生成建议
        
        Args:
            query_info: 查询信息
            problem: 问题对象
            table_schema: 表结构信息
            
        Returns:
            优化建议
        """
        problem_type = problem.problem_type
        sql = query_info.query_text
        
        # 根据问题类型生成建议
        if problem_type.name == "FULL_TABLE_SCAN":
            return self._suggest_index_optimization(query_info, problem)
        elif problem_type.name == "SELECT_STAR":
            return self._suggest_specific_columns(query_info, problem)
        elif problem_type.name == "LIKE_PREFIX_WILDCARD":
            return self._suggest_like_optimization(query_info, problem)
        elif problem_type.name == "OR_CONDITION":
            return self._suggest_or_replacement(query_info, problem)
        elif problem_type.name == "FUNCTION_IN_WHERE":
            return self._suggest_function_optimization(query_info, problem)
        elif problem_type.name == "TOO_MANY_ROWS":
            return self._suggest_row_reduction(query_info, problem)
        elif problem_type.name == "SUBQUERY_INEFFICIENT":
            return self._suggest_cte_or_join(query_info, problem)
        
        return None
    
    def _suggest_index_optimization(self, query_info, problem) -> OptimizationSuggestion:
        """建议索引优化"""
        sql = query_info.query_text
        
        # 提取 WHERE 条件中的列
        where_columns = self._extract_where_columns(sql)
        
        # 提取 ORDER BY 列
        order_columns = self._extract_order_columns(sql)
        
        # 提取 JOIN 列
        join_columns = self._extract_join_columns(sql)
        
        columns = where_columns + order_columns + join_columns
        columns = list(set(columns))  # 去重
        
        if not columns:
            columns = ["相关列"]
        
        index_create = f"""
-- 为表添加索引建议
CREATE INDEX idx_optimization ON your_table ({', '.join(columns)});
"""
        
        return OptimizationSuggestion(
            title="添加索引优化查询",
            description=f"查询执行时间过长（{query_info.execution_time:.2f}s），建议为相关列添加索引",
            priority="HIGH",
            category="INDEX",
            original_sql=sql,
            suggested_sql=index_create.strip(),
            estimated_improvement="预计可提升 50%-90% 的查询性能",
            implementation_notes=f"1. 确认 {', '.join(columns)} 列的选择性\n2. 考虑创建复合索引\n3. 分析索引的使用频率"
        )
    
    def _suggest_specific_columns(self, query_info, problem) -> OptimizationSuggestion:
        """建议指定列名"""
        sql = query_info.query_text
        
        # 尝试提取表名
        tables = self._extract_table_names(sql)
        if tables:
            table = tables[0]
            suggested_sql = f"-- 建议指定具体列名\nSELECT col1, col2, col3 FROM {table} WHERE ...;"
        else:
            suggested_sql = "-- 建议指定具体列名\nSELECT col1, col2, col3 FROM your_table WHERE ...;"
        
        return OptimizationSuggestion(
            title="避免使用 SELECT *",
            description="SELECT * 会返回所有列，增加 I/O 和网络传输开销",
            priority="MEDIUM",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql.strip(),
            estimated_improvement="减少 30%-70% 的数据传输量",
            implementation_notes="1. 只选择需要的列\n2. 避免返回大字段（如 TEXT/BLOB）\n3. 可以减少内存使用"
        )
    
    def _suggest_like_optimization(self, query_info, problem) -> OptimizationSuggestion:
        """建议优化 LIKE 查询"""
        sql = query_info.query_text
        
        suggested_sql = re.sub(
            r"LIKE\s+['\"]%",
            "LIKE '",
            sql,
            flags=re.IGNORECASE
        )
        
        return OptimizationSuggestion(
            title="优化 LIKE 查询",
            description="LIKE 使用前缀通配符（%xxx）无法使用索引",
            priority="HIGH",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql,
            estimated_improvement="索引命中率从 0% 提升到接近 100%",
            implementation_notes="1. 使用后缀通配符（xxx%）\n2. 或者考虑全文索引\n3. 或者使用倒排索引"
        )
    
    def _suggest_or_replacement(self, query_info, problem) -> OptimizationSuggestion:
        """建议用 UNION ALL 替代 OR"""
        sql = query_info.query_text
        
        # 简化的建议
        suggested_sql = f"""-- 建议使用 UNION ALL 替代 OR
SELECT * FROM table1 WHERE condition1
UNION ALL
SELECT * FROM table1 WHERE condition2;
"""
        
        return OptimizationSuggestion(
            title="用 UNION ALL 替代 OR",
            description="OR 条件可能导致索引失效，使用 UNION ALL 可能更高效",
            priority="LOW",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql.strip(),
            estimated_improvement="索引命中率可能提升 20%-50%",
            implementation_notes="1. 测试两种方式的性能\n2. 确保条件互斥时使用 UNION ALL\n3. 条件可能重叠时使用 UNION"
        )
    
    def _suggest_function_optimization(self, query_info, problem) -> OptimizationSuggestion:
        """建议优化 WHERE 子句中的函数"""
        sql = query_info.query_text
        
        suggested_sql = """-- 示例：将函数移到比较符号另一侧
-- 原始: WHERE YEAR(created_at) = 2023
-- 优化: WHERE created_at >= '2023-01-01' AND created_at < '2024-01-01'
"""
        
        return OptimizationSuggestion(
            title="避免 WHERE 子句中使用函数",
            description="函数会阻止索引使用，建议改写查询逻辑",
            priority="MEDIUM",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql.strip(),
            estimated_improvement="索引命中率可从 0% 提升到 100%",
            implementation_notes="1. 将函数应用到常量上\n2. 使用范围查询代替函数\n3. 考虑创建计算列索引"
        )
    
    def _suggest_row_reduction(self, query_info, problem) -> OptimizationSuggestion:
        """建议减少扫描行数"""
        sql = query_info.query_text
        
        suggested_sql = f"""-- 建议优化查询减少扫描行数
-- 当前扫描行数: {query_info.scan_rows_formatted}

1. 添加更精确的 WHERE 条件
2. 利用分区裁剪
3. 使用索引覆盖
4. 考虑数据分区策略
"""
        
        return OptimizationSuggestion(
            title="减少扫描行数",
            description=f"当前扫描 {query_info.scan_rows_formatted} 行，远超建议阈值",
            priority="HIGH",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql.strip(),
            estimated_improvement="可减少 50%-99% 的扫描行数",
            implementation_notes="1. 分析查询计划确定瓶颈\n2. 添加合适的 WHERE 条件\n3. 创建复合索引"
        )
    
    def _suggest_cte_or_join(self, query_info, problem) -> OptimizationSuggestion:
        """建议使用 CTE 或 JOIN"""
        sql = query_info.query_text
        
        suggested_sql = """-- 建议使用 CTE (WITH 子句) 或 JOIN
-- CTE 示例:
WITH cte1 AS (
    SELECT ... FROM table1 WHERE ...
),
cte2 AS (
    SELECT ... FROM table2 WHERE ...
)
SELECT ... FROM cte1 JOIN cte2 ON ...;
"""
        
        return OptimizationSuggestion(
            title="优化子查询为 CTE 或 JOIN",
            description="子查询可能导致性能问题，考虑使用 CTE 或 JOIN",
            priority="MEDIUM",
            category="QUERY",
            original_sql=sql,
            suggested_sql=suggested_sql.strip(),
            estimated_improvement="预计提升 20%-60% 的性能",
            implementation_notes="1. 评估子查询是否可转为 JOIN\n2. 使用 CTE 提高可读性\n3. 测试优化前后性能"
        )
    
    def _extract_where_columns(self, sql: str) -> List[str]:
        """提取 WHERE 条件中的列名"""
        columns = []
        # 简化的列名提取
        where_match = re.search(r'WHERE\s+([^;]+)', sql, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1)
            # 移除 ORDER BY 和 GROUP BY
            where_clause = re.split(r'ORDER BY|GROUP BY', where_clause, flags=re.IGNORECASE)[0]
            
            # 提取列名（简化）
            tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*[=<>!]', where_clause)
            columns.extend(tokens)
        
        return columns
    
    def _extract_order_columns(self, sql: str) -> List[str]:
        """提取 ORDER BY 列名"""
        columns = []
        order_match = re.search(r'ORDER BY\s+([^;]+)', sql, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            # 提取列名（简化，去除逗号和方向）
            tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', order_clause)
            columns.extend(tokens)
        
        return columns
    
    def _extract_join_columns(self, sql: str) -> List[str]:
        """提取 JOIN 条件中的列名"""
        columns = []
        join_match = re.findall(r'ON\s+([^;]+?)(?:JOIN|WHERE|GROUP BY|ORDER BY|$)', sql, re.IGNORECASE)
        for match in join_match:
            # 提取列名（简化）
            tokens = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', match)
            columns.extend(tokens)
        
        return columns
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """提取表名（简化版本）"""
        tables = []
        keywords = ['FROM', 'JOIN', 'INTO', 'UPDATE', 'TABLE']
        
        for keyword in keywords:
            pattern = rf'{keyword}\s+([^\s,;]+)'
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                table = match.strip('`"[]')
                if table and table.upper() not in ['WHERE', 'ON', 'SELECT', 'AS']:
                    tables.append(table)
        
        return list(set(tables))

