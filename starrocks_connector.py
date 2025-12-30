#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StarRocks 数据库连接器
提供 StarRocks 数据库连接和查询功能
"""

import pymysql
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """数据库连接配置"""
    host: str = "127.0.0.1"
    port: int = 9030
    user: str = "root"
    password: str = ""
    database: str = "information_schema"


class StarRocksConnector:
    """StarRocks 数据库连接器类"""
    
    def __init__(self, config: ConnectionConfig):
        """
        初始化连接器
        
        Args:
            config: 数据库连接配置
        """
        self.config = config
        self.connection = None
    
    def connect(self) -> bool:
        """
        建立数据库连接
        
        Returns:
            连接是否成功
        """
        try:
            self.connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"成功连接到 StarRocks: {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"连接 StarRocks 失败: {str(e)}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("已断开 StarRocks 连接")
    
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                result = cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            logger.error(f"SQL: {sql}")
            return []
    
    def execute_query_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        执行查询并返回单条结果
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            查询结果字典
        """
        results = self.execute_query(sql, params)
        return results[0] if results else None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            连接是否正常
        """
        try:
            result = self.execute_query_one("SELECT 1 as test")
            return result is not None and result.get('test') == 1
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            return False

