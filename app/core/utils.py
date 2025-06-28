"""
Utility functions for the application
"""

def convert_mongo_doc(doc: dict) -> dict:
    """
    Convert MongoDB document by replacing _id with id
    
    Args:
        doc: MongoDB document dictionary
        
    Returns:
        Modified dictionary with id instead of _id
    """
    if doc and "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


def convert_mongo_docs(docs: list) -> list:
    """
    Convert a list of MongoDB documents
    
    Args:
        docs: List of MongoDB document dictionaries
        
    Returns:
        List of modified dictionaries with id instead of _id
    """
    return [convert_mongo_doc(doc) for doc in docs if doc]