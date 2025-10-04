import psutil
from datetime import datetime
from typing import List

class SuricataProcess:
    def __init__(self, pid: int, cmdline: List[str]):
        self.pid = pid
        self.cmdline = cmdline
        self.start_time = datetime.fromtimestamp(psutil.Process(pid).create_time())
    
    @property
    def uptime(self) -> str:
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def is_alive(self) -> bool:
        try:
            return psutil.Process(self.pid).is_running()
        except psutil.NoSuchProcess:
            return False