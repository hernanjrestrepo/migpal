#!/usr/bin/env python3
"""
MigPAL Production Monitor v3.0.4
================================
Monitoreo continuo de producción:
- Detección de errores en tiempo real
- Métricas beta cada 24h
- Alertas automáticas
- Captura de contexto en crashes

USO:
    python scripts/production_monitor_v304.py [--once] [--metrics] [--watch]
    
    --once    Ejecutar una vez y salir
    --metrics Generar snapshot de métricas
    --watch   Monitoreo continuo (default)
"""

import os
import sys
import json
import time
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
LOG_FILE = Path(__file__).parent.parent / "logs" / "bot_v3.log"
METRICS_DIR = Path(__file__).parent.parent / "data" / "beta_metrics"
ALERTS_FILE = Path(__file__).parent.parent / "data" / "alerts.jsonl"
USER_DATA_DIR = Path(__file__).parent.parent / "data" / "users"

# Error patterns to monitor
ERROR_PATTERNS = [
    r"ERROR",
    r"Exception",
    r"Conflict",
    r"Traceback",
    r"TypeError",
    r"KeyError",
    r"AttributeError",
    r"NameError",
    r"ValueError",
    r"RuntimeError",
]

# Fallback patterns (generic errors shown to users)
FALLBACK_PATTERNS = [
    r"error inesperado",
    r"unexpected error",
    r"Ocurrió un error",
    r"An error occurred",
    r"Failed to send fallback",
]

# Phase definitions for metrics
PHASES = {
    "start": "Inicio",
    "name": "Nombre",
    "confirm_name": "Confirmar Nombre",
    "birth_date": "Fecha Nacimiento",
    "nationality": "Nacionalidad",
    "current_country": "País Actual",
    "current_city": "Ciudad Actual",
    "email": "Email",
    "phone": "Teléfono",
    "education_level": "Nivel Educativo",
    "education_status": "Estado Educativo",
    "education_field": "Campo Educativo",
    "education_career": "Carrera",
    "work_status": "Estado Laboral",
    "profession": "Profesión",
    "work_experience": "Experiencia",
    "english_level": "Nivel Inglés",
}


class ProductionMonitor:
    """Monitor de producción para MigPAL v3.0.4"""
    
    def __init__(self):
        self.errors_found = []
        self.fallbacks_found = []
        self.last_check_position = 0
        self.metrics = defaultdict(lambda: defaultdict(int))
        
        # Ensure directories exist
        METRICS_DIR.mkdir(parents=True, exist_ok=True)
        ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def check_errors(self) -> List[Dict[str, Any]]:
        """Check for errors in logs since last check"""
        errors = []
        
        if not LOG_FILE.exists():
            return errors
        
        with open(LOG_FILE, 'r') as f:
            # Seek to last position
            f.seek(self.last_check_position)
            
            for line in f:
                # Check for error patterns
                for pattern in ERROR_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        error = self._parse_error_line(line)
                        if error:
                            errors.append(error)
                        break
                
                # Check for fallback patterns
                for pattern in FALLBACK_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        fallback = self._parse_fallback_line(line)
                        if fallback:
                            self.fallbacks_found.append(fallback)
                        break
            
            # Update position
            self.last_check_position = f.tell()
        
        self.errors_found.extend(errors)
        return errors
    
    def _parse_error_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse an error line and extract context"""
        # Pattern: timestamp - module - level - message
        match = re.match(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([\w\.]+) - (\w+) - (.+)',
            line.strip()
        )
        
        if match:
            timestamp, module, level, message = match.groups()
            
            # Extract user_id if present
            user_match = re.search(r'user[=:](\d+)', message)
            user_id = user_match.group(1) if user_match else None
            
            # Extract state if present
            state_match = re.search(r'state[=:](\w+)', message)
            state = state_match.group(1) if state_match else None
            
            # Extract error type if present
            error_match = re.search(r'error[=:](\w+Error)', message)
            error_type = error_match.group(1) if error_match else level
            
            return {
                "timestamp": timestamp,
                "module": module,
                "level": level,
                "message": message,
                "user_id": user_id,
                "state": state,
                "error_type": error_type,
                "raw_line": line.strip()
            }
        
        return None
    
    def _parse_fallback_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a fallback line"""
        return self._parse_error_line(line)
    
    def log_alert(self, alert_type: str, details: Dict[str, Any]):
        """Log an alert to the alerts file"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "details": details
        }
        
        with open(ALERTS_FILE, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # Print to console
        print(f"🚨 ALERT [{alert_type}]: {json.dumps(details, indent=2)}")
    
    def generate_metrics_snapshot(self) -> Dict[str, Any]:
        """Generate a snapshot of beta metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "version": "v3.0.4",
            "period": "24h",
            "users": self._analyze_users(),
            "phases": self._analyze_phases(),
            "errors": self._analyze_errors(),
            "engagement": self._analyze_engagement(),
        }
        
        # Save to file
        filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = METRICS_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Metrics saved to: {filepath}")
        return metrics
    
    def _analyze_users(self) -> Dict[str, Any]:
        """Analyze user data"""
        users = {
            "total": 0,
            "active_24h": 0,
            "completed_profile": 0,
            "by_locale": defaultdict(int),
            "by_country": defaultdict(int),
        }
        
        if not USER_DATA_DIR.exists():
            return users
        
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        
        for user_file in USER_DATA_DIR.glob("*.json"):
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)
                
                users["total"] += 1
                
                # Check if active in last 24h
                if "last_activity" in data:
                    last_activity = datetime.fromisoformat(data["last_activity"])
                    if last_activity > day_ago:
                        users["active_24h"] += 1
                
                # Check profile completion
                profile = data.get("profile", {})
                personal = profile.get("personal", {})
                if personal.get("name") and personal.get("birth_date"):
                    users["completed_profile"] += 1
                
                # Locale
                locale = data.get("language", "en")
                users["by_locale"][locale] += 1
                
                # Country
                country = personal.get("current_country", "Unknown")
                users["by_country"][country] += 1
                
            except Exception as e:
                continue
        
        return users
    
    def _analyze_phases(self) -> Dict[str, Any]:
        """Analyze phase metrics from logs"""
        phases = {
            "transitions": defaultdict(int),
            "time_per_phase": defaultdict(list),
            "dropoffs": defaultdict(int),
        }
        
        if not LOG_FILE.exists():
            return phases
        
        # Parse state transitions from logs
        user_states = {}  # user_id -> (state, timestamp)
        
        with open(LOG_FILE, 'r') as f:
            for line in f:
                # Look for state changes
                if "state_change" in line or "TRANSITION" in line:
                    # Extract user and state
                    user_match = re.search(r'user[=:](\d+)', line)
                    state_match = re.search(r'State: (\w+)|→ (\w+)', line)
                    time_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    
                    if user_match and state_match and time_match:
                        user_id = user_match.group(1)
                        new_state = state_match.group(1) or state_match.group(2)
                        timestamp = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                        
                        # Calculate time in previous state
                        if user_id in user_states:
                            prev_state, prev_time = user_states[user_id]
                            duration = (timestamp - prev_time).total_seconds()
                            phases["time_per_phase"][prev_state].append(duration)
                            phases["transitions"][f"{prev_state} → {new_state}"] += 1
                        
                        user_states[user_id] = (new_state, timestamp)
        
        # Calculate averages
        avg_times = {}
        for phase, times in phases["time_per_phase"].items():
            if times:
                avg_times[phase] = sum(times) / len(times)
        phases["avg_time_per_phase"] = avg_times
        
        return phases
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error metrics"""
        return {
            "total_errors": len(self.errors_found),
            "total_fallbacks": len(self.fallbacks_found),
            "by_type": self._count_by_key(self.errors_found, "error_type"),
            "by_state": self._count_by_key(self.errors_found, "state"),
            "recent_errors": self.errors_found[-10:] if self.errors_found else [],
        }
    
    def _analyze_engagement(self) -> Dict[str, Any]:
        """Analyze engagement metrics"""
        engagement = {
            "messages_24h": 0,
            "callbacks_24h": 0,
            "commands_24h": 0,
            "avg_session_length": 0,
        }
        
        if not LOG_FILE.exists():
            return engagement
        
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        
        with open(LOG_FILE, 'r') as f:
            for line in f:
                # Check timestamp
                time_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if time_match:
                    try:
                        timestamp = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
                        if timestamp < day_ago:
                            continue
                    except:
                        continue
                
                # Count messages
                if "📩 MESSAGE" in line or "MSG:" in line:
                    engagement["messages_24h"] += 1
                
                # Count callbacks
                if "🔘 CALLBACK" in line or "CB:" in line:
                    engagement["callbacks_24h"] += 1
                
                # Count commands
                if "/start" in line or "/help" in line or "/nuevo" in line:
                    engagement["commands_24h"] += 1
        
        return engagement
    
    def _count_by_key(self, items: List[Dict], key: str) -> Dict[str, int]:
        """Count items by a specific key"""
        counts = defaultdict(int)
        for item in items:
            value = item.get(key, "unknown")
            counts[value] += 1
        return dict(counts)
    
    def print_status(self):
        """Print current status"""
        print("\n" + "=" * 60)
        print("🔍 MigPAL Production Monitor v3.0.4")
        print("=" * 60)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📁 Log file: {LOG_FILE}")
        print(f"📊 Metrics dir: {METRICS_DIR}")
        print()
        
        # Check for recent errors
        errors = self.check_errors()
        
        if errors:
            print(f"🚨 ERRORS FOUND: {len(errors)}")
            for error in errors[-5:]:
                print(f"  - [{error['timestamp']}] {error['error_type']}: {error['message'][:80]}...")
        else:
            print("✅ No new errors detected")
        
        if self.fallbacks_found:
            print(f"⚠️ FALLBACKS: {len(self.fallbacks_found)}")
        else:
            print("✅ No fallbacks detected")
        
        print()
    
    def watch(self, interval: int = 60):
        """Watch logs continuously"""
        print("👁️ Starting continuous monitoring...")
        print(f"   Checking every {interval} seconds")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                self.print_status()
                
                # Check for critical errors
                new_errors = self.check_errors()
                for error in new_errors:
                    if error["level"] == "ERROR" or "Exception" in error.get("error_type", ""):
                        self.log_alert("CRITICAL_ERROR", error)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    
    def run_once(self):
        """Run a single check"""
        self.print_status()
        
        # Check for errors
        errors = self.check_errors()
        
        if errors:
            print("\n📋 Error Details:")
            for error in errors:
                print(f"\n  Timestamp: {error['timestamp']}")
                print(f"  Type: {error['error_type']}")
                print(f"  User: {error.get('user_id', 'N/A')}")
                print(f"  State: {error.get('state', 'N/A')}")
                print(f"  Message: {error['message']}")
        
        return len(errors) == 0


def format_metrics_report(metrics: Dict[str, Any]) -> str:
    """Format metrics as a readable report"""
    lines = [
        "=" * 60,
        "📊 MigPAL Beta Metrics Snapshot",
        "=" * 60,
        f"📅 Generated: {metrics['timestamp']}",
        f"🏷️ Version: {metrics['version']}",
        f"⏱️ Period: {metrics['period']}",
        "",
        "👥 USERS",
        "-" * 40,
        f"  Total: {metrics['users']['total']}",
        f"  Active (24h): {metrics['users']['active_24h']}",
        f"  Completed Profile: {metrics['users']['completed_profile']}",
        "",
        "🌐 BY LOCALE",
    ]
    
    for locale, count in metrics['users']['by_locale'].items():
        lines.append(f"  {locale}: {count}")
    
    lines.extend([
        "",
        "📍 BY COUNTRY",
    ])
    
    for country, count in list(metrics['users']['by_country'].items())[:10]:
        lines.append(f"  {country}: {count}")
    
    lines.extend([
        "",
        "⏱️ AVG TIME PER PHASE (seconds)",
        "-" * 40,
    ])
    
    for phase, avg_time in metrics['phases'].get('avg_time_per_phase', {}).items():
        phase_name = PHASES.get(phase, phase)
        lines.append(f"  {phase_name}: {avg_time:.1f}s")
    
    lines.extend([
        "",
        "🔴 ERRORS",
        "-" * 40,
        f"  Total Errors: {metrics['errors']['total_errors']}",
        f"  Total Fallbacks: {metrics['errors']['total_fallbacks']}",
        "",
        "📈 ENGAGEMENT (24h)",
        "-" * 40,
        f"  Messages: {metrics['engagement']['messages_24h']}",
        f"  Callbacks: {metrics['engagement']['callbacks_24h']}",
        f"  Commands: {metrics['engagement']['commands_24h']}",
        "",
        "=" * 60,
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MigPAL Production Monitor v3.0.4")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--metrics", action="store_true", help="Generate metrics snapshot")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor()
    
    if args.metrics:
        metrics = monitor.generate_metrics_snapshot()
        print(format_metrics_report(metrics))
    elif args.once:
        success = monitor.run_once()
        sys.exit(0 if success else 1)
    else:
        # Default: watch mode
        monitor.watch(interval=args.interval)


if __name__ == "__main__":
    main()
