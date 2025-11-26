import os
import json

class ConfigManager:
    """Manages application configuration persistence"""
    
    def __init__(self):
        # Determine a persistent configuration directory (e.g., %APPDATA%/FastCut)
        self.config_dir = os.path.join(os.getenv('APPDATA', ''), 'FastCut')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        # Default values
        self.export_dir = ""
        self.playback_speed = "1.0x"
        self.use_keyframe_cut = True
        
        self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.export_dir = config.get("export_dir", "")
                    self.playback_speed = config.get("playback_speed", "1.0x")
                    self.use_keyframe_cut = config.get("use_keyframe_cut", True)
        except Exception as e:
            print(f"Failed to load config: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            config = {
                "export_dir": self.export_dir,
                "playback_speed": self.playback_speed,
                "use_keyframe_cut": self.use_keyframe_cut
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
