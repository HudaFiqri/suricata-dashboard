import os
from typing import Dict, List

class SuricataRuleManager:
    def __init__(self, rules_directory: str):
        self.rules_directory = rules_directory
    
    def get_rule_files(self) -> List[Dict[str, str]]:
        rule_files = []
        try:
            if not os.path.exists(self.rules_directory):
                return rule_files
            
            for filename in os.listdir(self.rules_directory):
                if filename.endswith('.rules'):
                    filepath = os.path.join(self.rules_directory, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        rule_files.append({
                            'filename': filename,
                            'filepath': filepath,
                            'content': content,
                            'rule_count': self._count_rules(content)
                        })
                    except Exception as e:
                        rule_files.append({
                            'filename': filename,
                            'filepath': filepath,
                            'content': f"Error reading file: {e}",
                            'rule_count': 0
                        })
        except Exception as e:
            raise IOError(f"Failed to read rules directory: {e}")
        
        return rule_files
    
    def save_rule_file(self, filename: str, content: str) -> None:
        if not filename.endswith('.rules'):
            filename += '.rules'
        
        filepath = os.path.join(self.rules_directory, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to save rule file: {e}")
    
    def delete_rule_file(self, filename: str) -> None:
        filepath = os.path.join(self.rules_directory, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            raise IOError(f"Failed to delete rule file: {e}")
    
    def _count_rules(self, content: str) -> int:
        lines = content.split('\n')
        count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if any(line.startswith(action) for action in ['alert', 'pass', 'drop', 'reject']):
                    count += 1
        return count