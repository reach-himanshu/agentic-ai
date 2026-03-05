import re

# The user's pasted string (with standard quotes)
raw_str = """[FunctionExecutionResult(content="([TextContent(type='text', text='Error searching knowledge base...', annotations=None, meta=None)], {'result': 'Error searching...'})", name='kb_search', call_id='call_123', is_error=False)]"""

# Another possibility of what AutoGen outputs:
raw_str2 = """[FunctionExecutionResult(content='Relevant information from Knowledge Base:\\nSource: doc.pdf\\nContent: The policy...', name='kb_search', call_id='call_123', is_error=False)]"""

def extract_content(msg_content):
    clean_content = msg_content
    if "FunctionExecutionResult(" in clean_content:
        # Try to find the content parameter
        match = re.search(r"FunctionExecutionResult\(content=(.*?),\s*name=", clean_content, re.DOTALL)
        if match:
            # The content group might be enclosed in quotes
            inner = match.group(1).strip()
            # If it starts with quote and ends with quote, strip them
            if (inner.startswith("'") and inner.endswith("'")) or (inner.startswith('"') and inner.endswith('"')):
                inner = inner[1:-1]
            
            # Now inner might still be a TextContent representation if the tool returned a tuple or complex object
            # Let's check if it has TextContent
            if "TextContent(type=" in inner and "text=" in inner:
                text_match = re.search(r"text=(?:'|\")(.*?)(?:'|\"), annotations=", inner, re.DOTALL)
                if text_match:
                    inner = text_match.group(1)
            
            clean_content = inner.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
    return clean_content

print("Test 1:", extract_content(raw_str))
print("Test 2:", extract_content(raw_str2))
