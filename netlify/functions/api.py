import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import mangum and the FastAPI app
from mangum import Mangum
from app.main import app

# Create the handler for Netlify
def handler(event, context):
    # Fix the path for Netlify Functions
    if 'path' in event:
        # Remove /.netlify/functions/api prefix
        path = event.get('path', '/')
        if path.startswith('/.netlify/functions/api'):
            event['path'] = path[22:] or '/'  # Remove the prefix
        
        # Also update rawPath if it exists
        if 'rawPath' in event:
            event['rawPath'] = event['path']
    
    # Create Mangum handler and process request
    mangum_handler = Mangum(app, lifespan="off", api_gateway_base_path="/")
    return mangum_handler(event, context)