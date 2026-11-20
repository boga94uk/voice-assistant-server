import os
import sys
sys.path.insert(0, 'src')
from utils import load_env

load_env()
key = os.getenv('OPENAI_API_KEY')
print(f'API Key loaded: {key[:10]}...' if key else 'API Key: NOT FOUND')
print(f'Key starts with sk-proj: {key.startswith("sk-proj") if key else False}')
