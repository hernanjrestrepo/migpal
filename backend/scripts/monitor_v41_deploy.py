#!/usr/bin/env python3
"""
MigPAL v4.1 Deploy Monitor
==========================
Monitorea logs durante 30 minutos post-deploy.
Detecta: errores middleware, loops, timeouts.
"""

import os
import sys
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

# Configuración
MONITOR_DURATION_MINUTES = 30
LOG_FILE = "/tmp/migpal_bot.log"
REPORT_FILE = "/workspace/hjrm/migpal/backend/reports/v41_deploy_monitor.json"

# Patrones a detectar
PATTERNS = {
    "error": r"(ERROR|error|Error|Exception|exception|FAILED|failed)",
    "v4_middleware": r"(V4|v4|middleware|MIGPAL_USA_STANDARD)",
    "loop": r"(loop|Loop|LOOP|repeated|infinite)",
    "timeout": r"(timeout|Timeout|TIMEOUT|timed out)",
    "gating": r"(gating|Gating|GATING|blocked|Blocked)",
    "warning": r"(WARNING|warning|Warning|WARN)",
}


class DeployMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=MONITOR_DURATION_MINUTES)
        self.events = defaultdict(list)
        self.stats = {
            "total_lines": 0,
            "errors": 0,
            "warnings": 0,
            "v4_events": 0,
            "loops_detected": 0,
            "timeouts": 0,
            "gating_events": 0,
        }
        self.last_position = 0
        
    def read_new_logs(self) -> List[str]:
        """Lee nuevas líneas del log"""
        try:
            with open(LOG_FILE, 'r') as f:
                f.seek(self.last_position)
                lines = f.readlines()
                self.last_position = f.tell()
                return lines
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading log: {e}")
            return []
    
    def analyze_line(self, line: str) -> Dict[str, bool]:
        """Analiza una línea de log"""
        results = {}
        for pattern_name, pattern in PATTERNS.items():
            results[pattern_name] = bool(re.search(pattern, line))
        return results
    
    def process_logs(self):
        """Procesa nuevos logs"""
        lines = self.read_new_logs()
        
        for line in lines:
            self.stats["total_lines"] += 1
            analysis = self.analyze_line(line)
            
            if analysis["error"]:
                self.stats["errors"] += 1
                self.events["errors"].append({
                    "time": datetime.now().isoformat(),
                    "line": line.strip()[:200]
                })
            
            if analysis["warning"]:
                self.stats["warnings"] += 1
            
            if analysis["v4_middleware"]:
                self.stats["v4_events"] += 1
                if analysis["error"]:
                    self.events["v4_errors"].append({
                        "time": datetime.now().isoformat(),
                        "line": line.strip()[:200]
                    })
            
            if analysis["loop"]:
                self.stats["loops_detected"] += 1
                self.events["loops"].append({
                    "time": datetime.now().isoformat(),
                    "line": line.strip()[:200]
                })
            
            if analysis["timeout"]:
                self.stats["timeouts"] += 1
                self.events["timeouts"].append({
                    "time": datetime.now().isoformat(),
                    "line": line.strip()[:200]
                })
            
            if analysis["gating"]:
                self.stats["gating_events"] += 1
    
    def get_status(self) -> str:
        """Obtiene estado actual"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        remaining = max(0, MONITOR_DURATION_MINUTES - elapsed)
        
        status = "🟢 HEALTHY"
        if self.stats["errors"] > 10:
            status = "🔴 CRITICAL"
        elif self.stats["errors"] > 5:
            status = "🟠 WARNING"
        elif self.stats["loops_detected"] > 0 or self.stats["timeouts"] > 3:
            status = "🟡 ATTENTION"
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║  MigPAL v4.1 Deploy Monitor                              ║
╠══════════════════════════════════════════════════════════╣
║  Status: {status:45s}║
║  Elapsed: {elapsed:5.1f} min | Remaining: {remaining:5.1f} min            ║
╠══════════════════════════════════════════════════════════╣
║  📊 STATS                                                ║
║  • Total lines: {self.stats['total_lines']:10d}                          ║
║  • Errors: {self.stats['errors']:10d}                               ║
║  • Warnings: {self.stats['warnings']:10d}                             ║
║  • V4 events: {self.stats['v4_events']:10d}                            ║
║  • Loops: {self.stats['loops_detected']:10d}                                ║
║  • Timeouts: {self.stats['timeouts']:10d}                             ║
║  • Gating: {self.stats['gating_events']:10d}                               ║
╚══════════════════════════════════════════════════════════╝
"""
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte final"""
        return {
            "monitor_id": f"v41_deploy_{self.start_time.strftime('%Y%m%d_%H%M%S')}",
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
            "stats": self.stats,
            "events": dict(self.events),
            "status": "PASSED" if self.stats["errors"] < 5 and self.stats["loops_detected"] == 0 else "FAILED",
            "p0_issues": [e for e in self.events.get("errors", []) if "critical" in e.get("line", "").lower()],
            "p1_issues": [e for e in self.events.get("v4_errors", [])],
        }
    
    def run(self, duration_minutes: int = None):
        """Ejecuta el monitor"""
        if duration_minutes:
            self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        print(f"🚀 Starting v4.1 deploy monitor...")
        print(f"   Duration: {MONITOR_DURATION_MINUTES} minutes")
        print(f"   Log file: {LOG_FILE}")
        print(f"   Report: {REPORT_FILE}")
        print()
        
        try:
            while datetime.now() < self.end_time:
                self.process_logs()
                print(self.get_status())
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n⚠️ Monitor interrupted by user")
        
        # Generate final report
        report = self.generate_report()
        
        os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Report saved: {REPORT_FILE}")
        print(f"\n{'='*60}")
        print(f"FINAL STATUS: {report['status']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"P0 Issues: {len(report['p0_issues'])}")
        print(f"P1 Issues: {len(report['p1_issues'])}")
        print(f"{'='*60}")
        
        return report


def quick_check():
    """Verificación rápida de 1 minuto"""
    monitor = DeployMonitor()
    return monitor.run(duration_minutes=1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_check()
    else:
        monitor = DeployMonitor()
        monitor.run()
