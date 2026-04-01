import urllib.request
import urllib.error
import json
from .config_mgr import load_config, save_config
from .constants import CATEGORIES

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def get_current_model():
    return load_config().get("ollama_model", "llama3.2")

def classify_job_title(role_name: str, model_name: str = None) -> str:
    """
    Sends a zero-shot prompt to the local Ollama instance to categorize the job title.
    """
    if not model_name:
        model_name = get_current_model()

    categories_text = "\n".join([f"- {c}" for c in CATEGORIES])
    
    prompt = f"""You are an expert technical recruiter matching job titles to standardized broad reporting categories.
You MUST map the given job title to EXACTLY ONE of the following predefined categories. Do not invent new categories.

Allowed Categories: 
{categories_text}

Reply with ONLY the exact string from the Allowed Categories list. Do not include any explanation, punctuation, or extra words.

Title: {role_name}
Category:"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0 # Strict answers only
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={"Content-Type": "application/json"})
    
    print(f"[LLM] Asking Ollama ({model_name}) to classify: '{role_name}' ... ", end="", flush=True)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            category = result.get('response', '').strip()
            
            # Additional safety cleanup in case the LLM ignored instructions
            category = category.strip('"').strip("'").strip('.')
            if not category:
                print("Failed (fallback to title case)")
                return role_name.title()
                
            print(f"Result: {category}")
            return category
    except urllib.error.URLError as e:
        print(f"\n[LLM Error] Ollama is not running or unreachable: {e}")
        return role_name.title()
    except Exception as e:
        print(f"\n[LLM Error] Error calling Ollama: {e}")
        return role_name.title()

def set_ollama_model(model_name: str):
    """Updates the default model used for classification in the config."""
    config = load_config()
    config["ollama_model"] = model_name
    save_config(config)

