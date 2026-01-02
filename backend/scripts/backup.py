#!/usr/bin/env python3
"""
MigPAL Backup Script
Crea backups automáticos de los datos de usuarios

Usage:
    python backup.py                    # Backup manual
    python backup.py --schedule         # Ejecutar con scheduler
    python backup.py --restore <file>   # Restaurar desde backup
"""

import os
import sys
import json
import shutil
import tarfile
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
MAX_BACKUPS = 30  # Keep last 30 backups
BACKUP_INTERVAL_HOURS = 6


def create_backup() -> str:
    """Create a backup of all data"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"migpal_backup_{timestamp}"
    backup_path = BACKUP_DIR / f"{backup_name}.tar.gz"
    
    logger.info(f"Creating backup: {backup_path}")
    
    try:
        # Create tar.gz archive
        with tarfile.open(backup_path, "w:gz") as tar:
            if DATA_DIR.exists():
                tar.add(DATA_DIR, arcname="data")
        
        # Get backup size
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Backup created: {backup_path} ({size_mb:.2f} MB)")
        
        # Create metadata file
        metadata = {
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "size_bytes": backup_path.stat().st_size,
            "files_count": count_files(DATA_DIR),
            "version": "5.1"
        }
        
        metadata_path = BACKUP_DIR / f"{backup_name}_meta.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Cleanup old backups
        cleanup_old_backups()
        
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        raise


def count_files(directory: Path) -> int:
    """Count files in directory recursively"""
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.rglob("*") if _.is_file())


def cleanup_old_backups():
    """Remove old backups keeping only MAX_BACKUPS"""
    if not BACKUP_DIR.exists():
        return
    
    backups = sorted(BACKUP_DIR.glob("migpal_backup_*.tar.gz"))
    
    if len(backups) > MAX_BACKUPS:
        to_delete = backups[:-MAX_BACKUPS]
        for backup in to_delete:
            try:
                backup.unlink()
                # Also delete metadata
                meta = backup.with_suffix("").with_suffix("_meta.json")
                if meta.exists():
                    meta.unlink()
                logger.info(f"Deleted old backup: {backup.name}")
            except Exception as e:
                logger.error(f"Error deleting {backup}: {e}")


def restore_backup(backup_file: str):
    """Restore data from a backup file"""
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        # Try in backup directory
        backup_path = BACKUP_DIR / backup_file
    
    if not backup_path.exists():
        logger.error(f"❌ Backup file not found: {backup_file}")
        return False
    
    logger.info(f"Restoring from: {backup_path}")
    
    # Create backup of current data before restore
    if DATA_DIR.exists():
        pre_restore_backup = DATA_DIR.parent / f"data_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(str(DATA_DIR), str(pre_restore_backup))
        logger.info(f"Current data backed up to: {pre_restore_backup}")
    
    try:
        # Extract backup
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(DATA_DIR.parent)
        
        logger.info(f"✅ Restore completed from: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        # Try to restore pre-restore backup
        if pre_restore_backup.exists():
            shutil.move(str(pre_restore_backup), str(DATA_DIR))
            logger.info("Rolled back to previous data")
        return False


def list_backups():
    """List all available backups"""
    if not BACKUP_DIR.exists():
        print("No backups found.")
        return
    
    backups = sorted(BACKUP_DIR.glob("migpal_backup_*.tar.gz"), reverse=True)
    
    if not backups:
        print("No backups found.")
        return
    
    print("\n📦 Available Backups:\n")
    print(f"{'#':<4} {'Date':<20} {'Size':<12} {'Files':<10}")
    print("-" * 50)
    
    for i, backup in enumerate(backups, 1):
        # Try to read metadata
        meta_path = backup.with_suffix("").with_suffix("_meta.json")
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            date = meta.get("datetime", "Unknown")[:19]
            files = meta.get("files_count", "?")
        else:
            date = backup.stem.replace("migpal_backup_", "")
            files = "?"
        
        size_mb = backup.stat().st_size / (1024 * 1024)
        print(f"{i:<4} {date:<20} {size_mb:.2f} MB{'':<4} {files:<10}")
    
    print(f"\nTotal: {len(backups)} backups")
    print(f"Location: {BACKUP_DIR}")


def run_scheduler():
    """Run backup on a schedule"""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
    except ImportError:
        logger.error("apscheduler not installed. Run: pip install apscheduler")
        return
    
    scheduler = BlockingScheduler()
    
    # Schedule backup every BACKUP_INTERVAL_HOURS
    scheduler.add_job(
        create_backup,
        'interval',
        hours=BACKUP_INTERVAL_HOURS,
        id='migpal_backup',
        name='MigPAL Data Backup'
    )
    
    # Also run immediately
    create_backup()
    
    logger.info(f"📅 Backup scheduler started (every {BACKUP_INTERVAL_HOURS} hours)")
    logger.info("Press Ctrl+C to stop")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")


def main():
    parser = argparse.ArgumentParser(description="MigPAL Backup Tool")
    parser.add_argument("--schedule", action="store_true", help="Run with scheduler")
    parser.add_argument("--restore", type=str, help="Restore from backup file")
    parser.add_argument("--list", action="store_true", help="List available backups")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.restore:
        restore_backup(args.restore)
    elif args.schedule:
        run_scheduler()
    else:
        # Manual backup
        backup_path = create_backup()
        print(f"\n✅ Backup created: {backup_path}")


if __name__ == "__main__":
    main()
