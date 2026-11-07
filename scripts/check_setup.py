import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai.retrieval import load_documents,retrieve
from ai.service import has_api_key
import db

db.initialize()
print('Database initialized')
print('Knowledge notes:',len(load_documents()))
print('Offline search results:',len(retrieve('newborn home visits schedule')))
print('OpenAI mode:', 'available' if has_api_key() else 'disabled; offline mode ready')
