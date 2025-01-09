import os
from dataclasses import dataclass
import yaml
from pathlib import Path

# Load configuration from YAML
@dataclass
class Config:
    SUPABASE_URL: str
    SUPABASE_KEY: str
    MAILJET_API_KEY: str
    MAILJET_API_SECRET: str

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'Config':
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        return cls(
            SUPABASE_URL=config_data['supabase']['url'],
            SUPABASE_KEY=config_data['supabase']['key'],
            MAILJET_API_KEY=config_data['mailjet']['api_key'],
            MAILJET_API_SECRET=config_data['mailjet']['secret_key']
        )

config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
config = Config.from_yaml(str(config_path))
