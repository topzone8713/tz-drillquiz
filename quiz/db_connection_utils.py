"""
데이터베이스 연결 상태 확인 유틸리티
"""

import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

def log_database_connection_info():
    """데이터베이스 연결 정보를 로깅합니다."""
    try:
        db_config = settings.DATABASES['default']
        logger.info("🔗 Database Connection Configuration:")
        logger.info(f"   ENGINE: {db_config['ENGINE']}")
        logger.info(f"   HOST: {db_config['HOST']}")
        logger.info(f"   PORT: {db_config['PORT']}")
        logger.info(f"   NAME: {db_config['NAME']}")
        logger.info(f"   USER: {db_config['USER']}")
        logger.info(f"   CONN_MAX_AGE: {db_config.get('CONN_MAX_AGE', 'Not set')}")
        
        if 'OPTIONS' in db_config:
            logger.info(f"   OPTIONS: {db_config['OPTIONS']}")
        
        if 'TEST' in db_config:
            test_config = db_config['TEST']
            logger.info(f"   TEST_NAME: {test_config.get('NAME', 'Not set')}")
            logger.info(f"   TEST_CONN_MAX_AGE: {test_config.get('CONN_MAX_AGE', 'Not set')}")
            logger.info(f"   TEST_OPTIONS: {test_config.get('OPTIONS', {})}")
        
        # 현재 연결 상태도 함께 로깅
        log_connection_state()
            
    except Exception as e:
        logger.error(f"❌ Failed to log database connection info: {e}")

def check_database_connection():
    """데이터베이스 연결 상태를 확인합니다."""
    try:
        # 연결 전 상태 로깅
        logger.info("🔍 Checking database connection...")
        logger.info(f"   Connection object: {connection.connection}")
        logger.info(f"   Closed: {getattr(connection, 'closed', 'N/A')}")
        logger.info(f"   In transaction: {connection.in_atomic_block}")
        logger.info(f"   Connection state: {getattr(connection.connection, 'closed', 'N/A') if connection.connection else 'No connection'}")
        
        # 연결이 끊어진 경우 재연결 시도
        if connection.connection and getattr(connection.connection, 'closed', False):
            logger.warning("⚠️  Connection is closed, attempting to reconnect...")
            connection.close()
            connection.connect()
            logger.info("🔄 Reconnection attempted")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                logger.info("✅ Database connection is healthy")
                logger.info(f"   Test query result: {result}")
                return True
            else:
                logger.error("❌ Database connection test failed")
                logger.error(f"   Unexpected result: {result}")
                return False
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error args: {e.args}")
        logger.error(f"   Connection state: {connection.connection}")
        logger.error(f"   Closed: {getattr(connection, 'closed', 'N/A')}")
        
        # 에러 발생 시점의 상세 컨텍스트 로깅
        log_error_context()
        return False

def log_connection_state():
    """현재 연결 상태를 로깅합니다."""
    try:
        if connection.connection:
            logger.info(f"🔗 Connection state: {connection.connection.get_backend_pid()}")
            logger.info(f"   Is connected: {not connection.connection.closed}")
            logger.info(f"   Connection age: {getattr(connection, 'age', 'Unknown')}")
        else:
            logger.warning("⚠️  No active database connection")
    except Exception as e:
        logger.error(f"❌ Failed to check connection state: {e}")

def log_error_context():
    """에러 발생 시점의 데이터베이스 연결 상태를 로깅합니다."""
    try:
        logger.error("🚨 ERROR CONTEXT - Database Connection State:")
        logger.error(f"   Connection object: {connection.connection}")
        logger.error(f"   Closed: {getattr(connection, 'closed', 'N/A')}")
        logger.error(f"   In transaction: {connection.in_atomic_block}")
        logger.error(f"   Connection age: {getattr(connection, 'age', 'Unknown')}")
        
        # 데이터베이스 설정 정보
        db_config = settings.DATABASES['default']
        logger.error(f"   DB HOST: {db_config['HOST']}")
        logger.error(f"   DB PORT: {db_config['PORT']}")
        logger.error(f"   DB NAME: {db_config['NAME']}")
        logger.error(f"   DB USER: {db_config['USER']}")
        logger.error(f"   CONN_MAX_AGE: {db_config.get('CONN_MAX_AGE', 'Not set')}")
        
        if 'OPTIONS' in db_config:
            logger.error(f"   DB OPTIONS: {db_config['OPTIONS']}")
            
    except Exception as e:
        logger.error(f"❌ Failed to log error context: {e}")
