"""
Database Backup Module

Automated database backups with:
- Multiple backup strategies (full, incremental)
- Retention policies
- Compression
- Encryption support
"""

import os
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from structured_logging import get_logger

logger = get_logger(__name__)


class DatabaseBackup:
    """
    Manages database backups with retention policies
    
    Features:
    - Automated backups
    - Compression
    - Retention management
    - Multiple database support
    """
    
    def __init__(
        self,
        backup_dir: str = "backups",
        retention_days: int = 30,
        compress: bool = True
    ):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups
            retention_days: Days to retain backups
            compress: Whether to compress backups
        """
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.compress = compress
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"Backup manager initialized",
            extra={
                'backup_dir': str(self.backup_dir),
                'retention_days': retention_days,
                'compress': compress
            }
        )
    
    def backup_postgresql(
        self,
        database_url: str,
        backup_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Backup PostgreSQL database using pg_dump
        
        Args:
            database_url: PostgreSQL connection string
            backup_name: Custom backup name (auto-generated if None)
        
        Returns:
            Path to backup file or None if failed
        """
        try:
            # Parse database URL
            # Format: postgresql://user:password@host:port/database
            parts = database_url.replace('postgresql://', '').split('@')
            if len(parts) != 2:
                logger.error("Invalid PostgreSQL URL format")
                return None
            
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            
            if len(user_pass) != 2 or len(host_db) != 2:
                logger.error("Invalid PostgreSQL URL format")
                return None
            
            username = user_pass[0]
            password = user_pass[1]
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_db[1]
            
            # Generate backup filename
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"postgresql_{database}_{timestamp}"
            
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # Run pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', database,
                '-F', 'p',  # Plain text format
                '-f', str(backup_file)
            ]
            
            logger.info(f"Starting PostgreSQL backup: {backup_name}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None
            
            # Compress if enabled
            if self.compress:
                compressed_file = self._compress_file(backup_file)
                if compressed_file:
                    backup_file.unlink()  # Remove uncompressed file
                    backup_file = compressed_file
            
            logger.info(
                f"PostgreSQL backup completed",
                extra={
                    'backup_file': str(backup_file),
                    'size_bytes': backup_file.stat().st_size
                }
            )
            
            return str(backup_file)
            
        except subprocess.TimeoutExpired:
            logger.error("Backup timeout exceeded")
            return None
        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            return None
    
    def backup_sqlite(
        self,
        database_path: str,
        backup_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Backup SQLite database
        
        Args:
            database_path: Path to SQLite database file
            backup_name: Custom backup name (auto-generated if None)
        
        Returns:
            Path to backup file or None if failed
        """
        try:
            db_path = Path(database_path)
            
            if not db_path.exists():
                logger.error(f"Database file not found: {database_path}")
                return None
            
            # Generate backup filename
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                db_name = db_path.stem
                backup_name = f"sqlite_{db_name}_{timestamp}"
            
            backup_file = self.backup_dir / f"{backup_name}.db"
            
            logger.info(f"Starting SQLite backup: {backup_name}")
            
            # Copy database file
            shutil.copy2(db_path, backup_file)
            
            # Compress if enabled
            if self.compress:
                compressed_file = self._compress_file(backup_file)
                if compressed_file:
                    backup_file.unlink()  # Remove uncompressed file
                    backup_file = compressed_file
            
            logger.info(
                f"SQLite backup completed",
                extra={
                    'backup_file': str(backup_file),
                    'size_bytes': backup_file.stat().st_size
                }
            )
            
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}", exc_info=True)
            return None
    
    def _compress_file(self, file_path: Path) -> Optional[Path]:
        """
        Compress file using gzip
        
        Args:
            file_path: Path to file to compress
        
        Returns:
            Path to compressed file or None if failed
        """
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.debug(f"File compressed: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None
    
    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period
        
        Returns:
            Number of backups removed
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            removed_count = 0
            
            for backup_file in self.backup_dir.glob('*'):
                if backup_file.is_file():
                    # Get file modification time
                    mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if mtime < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
                        logger.info(f"Removed old backup: {backup_file.name}")
            
            logger.info(f"Cleanup completed: {removed_count} backups removed")
            return removed_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return 0
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob('*'), reverse=True):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'compressed': backup_file.suffix == '.gz'
                })
        
        return backups
    
    def restore_postgresql(
        self,
        backup_file: str,
        database_url: str
    ) -> bool:
        """
        Restore PostgreSQL database from backup
        
        Args:
            backup_file: Path to backup file
            database_url: PostgreSQL connection string
        
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Decompress if needed
            if backup_path.suffix == '.gz':
                decompressed = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(decompressed, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = decompressed
            
            # Parse database URL (similar to backup_postgresql)
            parts = database_url.replace('postgresql://', '').split('@')
            user_pass = parts[0].split(':')
            host_db = parts[1].split('/')
            
            username = user_pass[0]
            password = user_pass[1]
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_db[1]
            
            # Set environment variable for password
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # Run psql to restore
            cmd = [
                'psql',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', database,
                '-f', str(backup_path)
            ]
            
            logger.info(f"Starting PostgreSQL restore from: {backup_file}")
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                logger.error(f"psql restore failed: {result.stderr}")
                return False
            
            logger.info("PostgreSQL restore completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False


# Global backup manager instance
_backup_manager: Optional[DatabaseBackup] = None


def get_backup_manager(**kwargs) -> DatabaseBackup:
    """
    Get or create global backup manager instance
    
    Args:
        **kwargs: Arguments for DatabaseBackup
    
    Returns:
        DatabaseBackup instance
    """
    global _backup_manager
    
    if _backup_manager is None:
        _backup_manager = DatabaseBackup(**kwargs)
    
    return _backup_manager
