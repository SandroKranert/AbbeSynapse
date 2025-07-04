import sys
import json
from web_search_agent import create_web_search_agent

if __name__ == "__main__":
    prompt = sys.argv[1]
    result = create_web_search_agent(prompt)
    print(json.dumps(result, ensure_ascii=False))
