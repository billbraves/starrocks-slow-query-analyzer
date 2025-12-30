#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
慢 SQL 收集器
从 StarRocks 收集慢查询数据
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import sqlparse
from starrocks_connector import StarRocksConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SlowQueryInfo:
    """慢查询信息"""
    query_id: str
    query_text: str
    database: str
    user: str
    execution_time: float  # 秒
    scan_rows: int
    scan_bytes: int
    memory_used: int
    cpu_time: float
    start_time: datetime
    end_time: datetime
    peak_memory: int = 0
    rows_returned: int = 0
    
    @property
    def execution_time_ms(self) -> float:
        """执行时间（毫秒）"""
        return self.execution_time * 1000
    
    @property
    def scan_rows_formatted(self) -> str:
        """格式化扫描行数"""
        if self.scan_rows >= 100000000:
            return f"{self.scan_rows / 100000000:.2f} 亿"
        elif self.scan_rows >= 10000:
            return f"{self.scan_rows / 10000:.2f} 万"
        return str(self.scan_rows)
    
    @property
    def scan_bytes_formatted(self) -> str:
        """格式化扫描字节数"""
        if self.scan_bytes >= 1073741824:
            return f"{self.scan_bytes / 1073741824:.2f} GB"
        elif self.scan_bytes >= 1048576:
            return f"{self.scan_bytes / 1048576:.2f} MB"
        elif self.scan_bytes >= 1024:
            return f"{self.scan_bytes / 1024:.2f} KB"
        return f"{self.scan_bytes} B"
    
    @property
    def severity(self) -> str:
        """严重程度"""
        if self.execution_time >= 10.0:
            return "CRITICAL"
        elif self.execution_time >= 5.0:
            return "HIGH"
        elif self.execution_time >= 1.0:
            return "MEDIUM"
        return "LOW"


class SlowQueryCollector:
    """慢查询收集器"""
    
    def __init__(self, connector: StarRocksConnector):
        """
        初始化收集器
        
        Args:
            connector: StarRocks 连接器
        """
        self.connector = connector
    
    def collect_slow_queries(
        self,
        time_range_hours: int = 24,
        min_execution_time: float = 1.0,
        database_filter: Optional[str] = None,
        user_filter: Optional[str] = None
    ) -> List[SlowQueryInfo]:
        """
        收集慢查询
        
        Args:
            time_range_hours: 时间范围（小时）
            min_execution_time: 最小执行时间（秒）
            database_filter: 数据库名称过滤
            user_filter: 用户名过滤
            
        Returns:
            慢查询列表
        """
        start_time = datetime.now() - timedelta(hours=time_range_hours)
        
        # 查询慢 SQL 的 SQL
        query = """
        SELECT
            query_id,
            query_text,
            database,
            user,
            query_time_seconds as execution_time,
            scan_rows,
            scan_bytes,
            memory_used_bytes as memory_used,
            cpu_time_ns / 1000000000 as cpu_time,
            start_time,
            end_time,
            peak_memory_bytes as peak_memory,
            rows_returned
        FROM information_schema.query_log
        WHERE start_time >= %s
          AND query_time_seconds >= %s
          AND query_text IS NOT NULL
          AND LENGTH(query_text) > 10
        """
        
        params = [start_time, min_execution_time]
        
        if database_filter:
            query += " AND database = %s"
            params.append(database_filter)
        
        if user_filter:
            query += " AND user = %s"
            params.append(user_filter)
        
        query += " ORDER BY query_time_seconds DESC LIMIT 1000"
        
        results = self.connector.execute_query(query, tuple(params))
        
        slow_queries = []
        for row in results:
            try:
                query_info = SlowQueryInfo(
                    query_id=row['query_id'],
                    query_text=row['query_text'],
                    database=row.get('database', ''),
                    user=row.get('user', ''),
                    execution_time=float(row.get('execution_time', 0)),
                    scan_rows=int(row.get('scan_rows', 0)),
                    scan_bytes=int(row.get('scan_bytes', 0)),
                    memory_used=int(row.get('memory_used', 0)),
                    cpu_time=float(row.get('cpu_time', 0)),
                    start_time=row.get('start_time', datetime.now()),
                    end_time=row.get('end_time', datetime.now()),
                    peak_memory=int(row.get('peak_memory', 0)),
                    rows_returned=int(row.get('rows_returned', 0))
                )
                slow_queries.append(query_info)
            except Exception as e:
                logger.warning(f"解析慢查询失败: {str(e)}")
                continue
        
        logger.info(f"收集到 {len(slow_queries)} 条慢查询")
        return slow_queries
    
    def get_query_statistics(self, slow_queries: List[SlowQueryInfo]) -> Dict[str, Any]:
        """
        获取慢查询统计信息
        
        Args:
            slow_queries: 慢查询列表
            
        Returns:
            统计信息字典
        """
        if not slow_queries:
            return {
                "total_queries": 0,
                "avg_execution_time": 0,
                "max_execution_time": 0,
                "total_scan_rows": 0,
                "total_scan_bytes": 0,
                "severity_distribution": {}
            }
        
        total_time = sum(q.execution_time for q in slow_queries)
        max_time = max(q.execution_time for q in slow_queries)
        total_scan_rows = sum(q.scan_rows for q in slow_queries)
        total_scan_bytes = sum(q.scan_bytes for q in slow_queries)
        
        severity_distribution = {}
        for q in slow_queries:
            severity = q.severity
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        return {
            "total_queries": len(slow_queries),
            "avg_execution_time": total_time / len(slow_queries),
            "max_execution_time": max_time,
            "total_scan_rows": total_scan_rows,
            "total_scan_bytes": total_scan_bytes,
            "severity_distribution": severity_distribution
        }
    
    def filter_by_pattern(self, queries: List[SlowQueryInfo], pattern: str) -> List[SlowQueryInfo]:
        """
        根据 SQL 模式过滤查询
        
        Args:
            queries: 查询列表
            pattern: 匹配模式（SQL 关键字或表名）
            
        Returns:
            过滤后的查询列表
        """
        pattern = pattern.upper()
        filtered = [
            q for q in queries 
            if pattern in q.query_text.upper()
        ]
        logger.info(f"模式 '{pattern}' 过滤后剩余 {len(filtered)} 条查询")
        return filtered
    
    def group_by_table(self, queries: List[SlowQueryInfo]) -> Dict[str, List[SlowQueryInfo]]:
        """
        按表分组查询
        
        Args:
            queries: 查询列表
            
        Returns:
            按表分组的查询字典
        """
        table_groups = {}
        
        for query in queries:
            try:
                # 简单的表名提取（基于 FROM/JOIN 子句）
                parsed = sqlparse.parse(query.query_text)[0]
                tables = []
                
                for token in parsed.flatten():
                    if token.ttype is None and token.value.upper() in ('FROM', 'JOIN', 'INTO', 'UPDATE'):
                        # 获取表名
                        next_tokens = list(token.flatten())
                        for i, t in enumerate(next_tokens):
                            if t.value.upper() in ('FROM', 'JOIN', 'INTO', 'UPDATE'):
                                if i + 2 < len(next_tokens):
                                    table = next_tokens[i + 2].value.strip('`"[]')
                                    if table and table.upper() not in ('WHERE', 'ON', 'SELECT'):
                                        tables.append(table)
                
                for table in tables:
                    if table not in table_groups:
                        table_groups[table] = []
                    table_groups[table].append(query)
            except Exception as e:
                logger.debug(f"提取表名失败: {str(e)}")
                continue
        
        return table_groups

