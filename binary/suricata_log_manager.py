import os
import json
from typing import Dict, List, Optional, Any

class SuricataLogManager:
    def __init__(self, log_directory: str):
        self.log_directory = log_directory
    
    def get_fast_log(self, lines: int = 100) -> List[str]:
        fast_log_path = os.path.join(self.log_directory, 'fast.log')
        return self._read_log_file(fast_log_path, lines)
    
    def get_eve_log(self, lines: int = 100) -> List[Dict[str, Any]]:
        eve_log_path = os.path.join(self.log_directory, 'eve.json')
        log_lines = self._read_log_file(eve_log_path, lines)
        
        json_logs = []
        for line in log_lines:
            try:
                json_logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        
        return json_logs
    
    def get_stats_log(self) -> Optional[Dict[str, Any]]:
        stats_log_path = os.path.join(self.log_directory, 'stats.log')
        try:
            with open(stats_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return None
    
    def _read_log_file(self, filepath: str, lines: int) -> List[str]:
        try:
            if not os.path.exists(filepath):
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]
        except Exception:
            return []