#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StarRocks 慢 SQL 分析主程序
整合所有模块，提供完整的慢 SQL 分析功能
"""

import yaml
import argparse
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from starrocks_connector import StarRocksConnector, ConnectionConfig
from slow_query_collector import SlowQueryCollector
from query_analyzer import QueryAnalyzer
from optimization_suggester import OptimizationSuggester
from report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StarRocksSlowQueryAnalyzer:
    """StarRocks 慢 SQL 分析器主类"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化分析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 初始化各个组件
        conn_config = ConnectionConfig(**self.config.get('database', {}))
        self.connector = StarRocksConnector(conn_config)
        
        self.collector = SlowQueryCollector(self.connector)
        self.analyzer = QueryAnalyzer(self.config.get('optimization', {}))
        self.suggester = OptimizationSuggester(self.config.get('optimization', {}))
        self.report_generator = ReportGenerator(self.config.get('output', {}))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"配置文件加载成功: {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._default_config()
        except Exception as e:
            logger.error(f"配置文件加载失败: {str(e)}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置"""
        return {
            'database': {
                'host': '127.0.0.1',
                'port': 9030,
                'user': 'root',
                'password': '',
                'database': 'information_schema'
            },
            'slow_query_threshold': 1.0,
            'analysis_time_range': 24,
            'output': {
                'report_dir': './reports',
                'report_format': 'html',
                'include_query_plans': True
            },
            'optimization': {
                'max_scan_rows': 10000000,
                'max_scan_bytes': 1073741824,
                'suggest_indexes': True
            }
        }
    
    def analyze(
        self,
        time_range_hours: Optional[int] = None,
        min_execution_time: Optional[float] = None,
        database_filter: Optional[str] = None,
        user_filter: Optional[str] = None,
        pattern_filter: Optional[str] = None
    ) -> str:
        """
        执行慢 SQL 分析
        
        Args:
            time_range_hours: 时间范围（小时）
            min_execution_time: 最小执行时间（秒）
            database_filter: 数据库名称过滤
            user_filter: 用户名过滤
            pattern_filter: SQL 模式过滤
            
        Returns:
            报告文件路径
        """
        # 使用配置或参数
        time_range = time_range_hours or self.config.get('analysis_time_range', 24)
        threshold = min_execution_time or self.config.get('slow_query_threshold', 1.0)
        
        logger.info(f"开始分析慢 SQL - 时间范围: {time_range}小时, 阈值: {threshold}秒")
        
        # 连接数据库
        if not self.connector.connect():
            raise Exception("无法连接到 StarRocks 数据库")
        
        try:
            # 收集慢查询
            slow_queries = self.collector.collect_slow_queries(
                time_range_hours=time_range,
                min_execution_time=threshold,
                database_filter=database_filter,
                user_filter=user_filter
            )
            
            # 模式过滤
            if pattern_filter:
                slow_queries = self.collector.filter_by_pattern(slow_queries, pattern_filter)
            
            if not slow_queries:
                logger.info("没有发现慢查询")
                return "无慢查询"
            
            # 获取统计信息
            statistics = self.collector.get_query_statistics(slow_queries)
            logger.info(f"收集到 {statistics['total_queries']} 条慢查询")
            
            # 分析每个查询
            problems_by_query = {}
            suggestions_by_query = {}
            
            for query in slow_queries:
                try:
                    # 分析问题
                    problems = self.analyzer.analyze_query(query)
                    problems_by_query[query.query_id] = problems
                    
                    # 生成建议
                    suggestions = self.suggester.generate_suggestions(query, problems)
                    suggestions_by_query[query.query_id] = suggestions
                    
                except Exception as e:
                    logger.warning(f"分析查询失败: {query.query_id}, 错误: {str(e)}")
                    continue
            
            # 生成报告
            metadata = {
                'time_range': time_range,
                'threshold': threshold,
                'database': database_filter,
                'user': user_filter,
                'pattern': pattern_filter
            }
            
            report_path = self.report_generator.generate_report(
                slow_queries=slow_queries,
                statistics=statistics,
                problems_by_query=problems_by_query,
                suggestions_by_query=suggestions_by_query,
                metadata=metadata
            )
            
            logger.info(f"分析完成，报告已生成: {report_path}")
            return report_path
        
        finally:
            self.connector.disconnect()
    
    def get_top_slow_queries(
        self,
        limit: int = 10,
        time_range_hours: int = 24,
        database: Optional[str] = None
    ) -> list:
        """
        获取最慢的查询
        
        Args:
            limit: 返回数量
            time_range_hours: 时间范围
            database: 数据库过滤
            
        Returns:
            慢查询列表
        """
        threshold = self.config.get('slow_query_threshold', 1.0)
        
        if not self.connector.connect():
            return []
        
        try:
            queries = self.collector.collect_slow_queries(
                time_range_hours=time_range_hours,
                min_execution_time=threshold,
                database_filter=database
            )
            
            return queries[:limit]
        
        finally:
            self.connector.disconnect()
    
    def analyze_specific_sql(self, sql: str) -> Dict[str, Any]:
        """
        分析特定的 SQL 语句
        
        Args:
            sql: SQL 语句
            
        Returns:
            分析结果字典
        """
        from slow_query_collector import SlowQueryInfo
        from datetime import timedelta
        
        # 创建虚拟查询对象
        query_info = SlowQueryInfo(
            query_id="manual_analysis",
            query_text=sql,
            database="",
            user="manual",
            execution_time=0,
            scan_rows=0,
            scan_bytes=0,
            memory_used=0,
            cpu_time=0,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1)
        )
        
        # 分析问题
        problems = self.analyzer.analyze_query(query_info)
        
        # 生成建议
        suggestions = self.suggester.generate_suggestions(query_info, problems)
        
        return {
            'sql': sql,
            'problems': [
                {
                    'type': p.problem_type.value,
                    'severity': p.severity,
                    'description': p.description,
                    'suggestion': p.suggestion
                }
                for p in problems
            ],
            'suggestions': [
                {
                    'title': s.title,
                    'priority': s.priority,
                    'description': s.description,
                    'suggested_sql': s.suggested_sql,
                    'estimated_improvement': s.estimated_improvement,
                    'implementation_notes': s.implementation_notes
                }
                for s in suggestions
            ]
        }


def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(description='StarRocks 慢 SQL 分析工具')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    parser.add_argument('--time-range', '-t', type=int, help='分析时间范围（小时）')
    parser.add_argument('--threshold', type=float, help='慢查询阈值（秒）')
    parser.add_argument('--database', '-d', help='数据库名称过滤')
    parser.add_argument('--user', '-u', help='用户名过滤')
    parser.add_argument('--pattern', '-p', help='SQL 模式过滤')
    parser.add_argument('--format', '-f', choices=['html', 'markdown', 'json'], help='报告格式')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = StarRocksSlowQueryAnalyzer(args.config)
    
    # 覆盖配置
    if args.format:
        analyzer.report_generator.report_format = args.format
    
    # 执行分析
    try:
        report_path = analyzer.analyze(
            time_range_hours=args.time_range,
            min_execution_time=args.threshold,
            database_filter=args.database,
            user_filter=args.user,
            pattern_filter=args.pattern
        )
        
        print(f"\n✅ 分析完成！")
        print(f"📄 报告路径: {report_path}")
        
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()

