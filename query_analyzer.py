#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL 查询分析器
分析 SQL 性能问题并生成诊断报告
"""

import sqlparse
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    SHOW = "SHOW"
    EXPLAIN = "EXPLAIN"
    OTHER = "OTHER"


class ProblemType(Enum):
    """问题类型"""
    FULL_TABLE_SCAN = "全表扫描"
    NO_INDEX = "缺少索引"
    TOO_MANY_ROWS = "扫描行数过多"
    MEMORY_INTENSIVE = "内存使用过高"
    JOIN_INEFFICIENT = "JOIN 低效"
    SUBQUERY_INEFFICIENT = "子查询低效"
    ORDERBY_EXPENSIVE = "ORDER BY 昂贵"
    GROUPBY_EXPENSIVE = "GROUP BY 昂贵"
    LARGE_RESULT_SET = "结果集过大"
    NO_WHERE_CLAUSE = "缺少 WHERE 条件"
    SELECT_STAR = "使用 SELECT *"
    OR_CONDITION = "使用 OR 条件"
    LIKE_PREFIX_WILDCARD = "LIKE 前缀通配符"
    FUNCTION_IN_WHERE = "WHERE 子句中使用函数"


@dataclass
class QueryProblem:
    """查询问题"""
    problem_type: ProblemType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    suggestion: str
    evidence: str


class QueryAnalyzer:
    """查询分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.max_scan_rows = self.config.get('max_scan_rows', 10000000)
        self.max_scan_bytes = self.config.get('max_scan_bytes', 1073741824)
    
    def analyze_query(self, query_info, execution_plan: Optional[Dict] = None) -> List[QueryProblem]:
        """
        分析查询并识别问题
        
        Args:
            query_info: 查询信息
            execution_plan: 执行计划
            
        Returns:
            问题列表
        """
        problems = []
        
        # 1. 分析执行时间
        problems.extend(self._analyze_execution_time(query_info))
        
        # 2. 分析扫描数据量
        problems.extend(self._analyze_scan_data(query_info))
        
        # 3. 分析 SQL 结构
        problems.extend(self._analyze_sql_structure(query_info))
        
        # 4. 分析执行计划（如果有）
        if execution_plan:
            problems.extend(self._analyze_execution_plan(execution_plan))
        
        return problems
    
    def _analyze_execution_time(self, query_info) -> List[QueryProblem]:
        """分析执行时间"""
        problems = []
        
        if query_info.execution_time >= 10.0:
            problems.append(QueryProblem(
                problem_type=ProblemType.FULL_TABLE_SCAN,
                severity="CRITICAL",
                description=f"查询执行时间过长: {query_info.execution_time:.2f} 秒",
                suggestion="检查是否有全表扫描，考虑添加索引或优化查询逻辑",
                evidence=f"执行时间: {query_info.execution_time:.2f}s"
            ))
        elif query_info.execution_time >= 5.0:
            problems.append(QueryProblem(
                problem_type=ProblemType.FULL_TABLE_SCAN,
                severity="HIGH",
                description=f"查询执行时间较长: {query_info.execution_time:.2f} 秒",
                suggestion="分析查询计划，检查是否需要优化",
                evidence=f"执行时间: {query_info.execution_time:.2f}s"
            ))
        
        return problems
    
    def _analyze_scan_data(self, query_info) -> List[QueryProblem]:
        """分析扫描数据量"""
        problems = []
        
        # 扫描行数过多
        if query_info.scan_rows > self.max_scan_rows:
            problems.append(QueryProblem(
                problem_type=ProblemType.TOO_MANY_ROWS,
                severity="HIGH",
                description=f"扫描行数过多: {query_info.scan_rows_formatted}",
                suggestion="考虑添加合适的 WHERE 条件或索引，减少扫描行数",
                evidence=f"扫描行数: {query_info.scan_rows}"
            ))
        
        # 扫描字节数过多
        if query_info.scan_bytes > self.max_scan_bytes:
            problems.append(QueryProblem(
                problem_type=ProblemType.TOO_MANY_ROWS,
                severity="HIGH",
                description=f"扫描数据量过大: {query_info.scan_bytes_formatted}",
                suggestion="只查询需要的列，避免 SELECT *，考虑分区裁剪",
                evidence=f"扫描字节数: {query_info.scan_bytes}"
            ))
        
        # 内存使用过高
        if query_info.memory_used > 536870912:  # 512MB
            problems.append(QueryProblem(
                problem_type=ProblemType.MEMORY_INTENSIVE,
                severity="MEDIUM",
                description=f"内存使用较高: {query_info.memory_used / 1048576:.2f} MB",
                suggestion="考虑增加内存限制、优化查询或调整执行引擎参数",
                evidence=f"内存使用: {query_info.memory_used / 1048576:.2f} MB"
            ))
        
        return problems
    
    def _analyze_sql_structure(self, query_info) -> List[QueryProblem]:
        """分析 SQL 结构"""
        problems = []
        sql = query_info.query_text.upper()
        
        try:
            parsed = sqlparse.parse(query_info.query_text)[0]
            
            # 检查 SELECT *
            if 'SELECT *' in sql:
                problems.append(QueryProblem(
                    problem_type=ProblemType.SELECT_STAR,
                    severity="MEDIUM",
                    description="使用 SELECT * 可能会返回不必要的列",
                    suggestion="明确指定需要的列，减少数据传输和内存使用",
                    evidence="SELECT *"
                ))
            
            # 检查 OR 条件
            if re.search(r'\bOR\b', sql) and 'WHERE' in sql:
                problems.append(QueryProblem(
                    problem_type=ProblemType.OR_CONDITION,
                    severity="LOW",
                    description="使用 OR 条件可能导致索引失效",
                    suggestion="考虑使用 UNION ALL 代替 OR，或优化查询逻辑",
                    evidence="发现 OR 条件"
                ))
            
            # 检查 LIKE 前缀通配符
            if re.search(r'LIKE\s+[\'"]%[^%]', sql):
                problems.append(QueryProblem(
                    problem_type=ProblemType.LIKE_PREFIX_WILDCARD,
                    severity="HIGH",
                    description="LIKE 使用前缀通配符 %... 无法使用索引",
                    suggestion="避免前缀通配符，考虑使用全文索引或倒排索引",
                    evidence="LIKE '%...'"
                ))
            
            # 检查 WHERE 子句中的函数
            where_match = re.search(r'WHERE\s+([^;]+)', sql)
            if where_match:
                where_clause = where_match.group(1)
                if re.search(r'[A-Z_]+\([^)]+\)', where_clause):
                    problems.append(QueryProblem(
                        problem_type=ProblemType.FUNCTION_IN_WHERE,
                        severity="MEDIUM",
                        description="WHERE 子句中使用函数可能导致索引失效",
                        suggestion="将函数移到比较符号的另一侧，或使用计算列索引",
                        evidence="WHERE 子句包含函数"
                    ))
            
            # 检查是否缺少 WHERE 条件
            has_where = 'WHERE' in sql
            has_join = 'JOIN' in sql
            is_select = sql.startswith('SELECT')
            
            if is_select and not has_where and not has_join:
                # 检查是否是简单的 SELECT COUNT(*) 或聚合查询
                if not re.search(r'(COUNT|SUM|AVG|MAX|MIN)\(', sql):
                    problems.append(QueryProblem(
                        problem_type=ProblemType.NO_WHERE_CLAUSE,
                        severity="HIGH",
                        description="SELECT 查询缺少 WHERE 条件",
                        suggestion="添加 WHERE 条件限制数据范围，避免全表扫描",
                        evidence="缺少 WHERE 条件"
                    ))
            
            # 检查子查询
            if re.search(r'FROM\s*\([^)]+SELECT', sql, re.IGNORECASE):
                problems.append(QueryProblem(
                    problem_type=ProblemType.SUBQUERY_INEFFICIENT,
                    severity="MEDIUM",
                    description="发现子查询，可能影响性能",
                    suggestion="考虑使用 CTE (WITH 子句) 或 JOIN 替代子查询",
                    evidence="发现子查询"
                ))
        
        except Exception as e:
            logger.warning(f"SQL 结构分析失败: {str(e)}")
        
        return problems
    
    def _analyze_execution_plan(self, execution_plan: Dict) -> List[QueryProblem]:
        """分析执行计划"""
        problems = []
        
        # 这里可以根据实际执行计划结构进行分析
        # 示例：检查全表扫描
        plan_str = str(execution_plan).upper()
        
        if 'OLAP_SCAN' in plan_str or 'FULL_SCAN' in plan_str:
            problems.append(QueryProblem(
                problem_type=ProblemType.FULL_TABLE_SCAN,
                severity="MEDIUM",
                description="执行计划显示可能存在全表扫描",
                suggestion="检查是否可以利用索引或分区裁剪",
                evidence="执行计划包含全表扫描"
            ))
        
        return problems
    
    def get_query_type(self, query_text: str) -> QueryType:
        """
        获取查询类型
        
        Args:
            query_text: SQL 查询文本
            
        Returns:
            查询类型
        """
        text = query_text.strip().upper()
        
        if text.startswith('SELECT'):
            return QueryType.SELECT
        elif text.startswith('INSERT'):
            return QueryType.INSERT
        elif text.startswith('UPDATE'):
            return QueryType.UPDATE
        elif text.startswith('DELETE'):
            return QueryType.DELETE
        elif text.startswith('CREATE'):
            return QueryType.CREATE
        elif text.startswith('ALTER'):
            return QueryType.ALTER
        elif text.startswith('DROP'):
            return QueryType.DROP
        elif text.startswith('SHOW'):
            return QueryType.SHOW
        elif text.startswith('EXPLAIN'):
            return QueryType.EXPLAIN
        else:
            return QueryType.OTHER
    
    def extract_tables(self, query_text: str) -> List[str]:
        """
        提取 SQL 中的表名
        
        Args:
            query_text: SQL 查询文本
            
        Returns:
            表名列表
        """
        tables = []
        try:
            parsed = sqlparse.parse(query_text)[0]
            
            keywords = ['FROM', 'JOIN', 'INTO', 'UPDATE', 'TABLE']
            
            for token in parsed.flatten():
                if token.ttype is None and token.value.upper() in keywords:
                    # 尝试获取下一个 token 作为表名
                    continue
            
            # 简化的表名提取
            text = query_text.upper()
            for keyword in keywords:
                pattern = rf'{keyword}\s+([^\s,;]+)'
                matches = re.findall(pattern, text)
                for match in matches:
                    table = match.strip('`"[]')
                    if table and table.upper() not in ['WHERE', 'ON', 'SELECT', 'AS']:
                        tables.append(table)
        
        except Exception as e:
            logger.warning(f"提取表名失败: {str(e)}")
        
        # 去重
        return list(set(tables))

