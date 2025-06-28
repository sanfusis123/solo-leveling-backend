import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import mangum and the FastAPI app
from mangum import Mangum
from app.main import app

# Create the handler for Netlify
handler = Mangum(app, lifespan="off")

# Netlify expects a specific function signature
def handler_wrapper(event, context):
    # Add base path for API Gateway compatibility
    if 'path' in event:
        # Remove /.netlify/functions/api prefix if present
        path = event['path']
        if path.startswith('/.netlify/functions/api'):
            event['path'] = path.replace('/.netlify/functions/api', '', 1) or '/'
    
    return handler(event, context)