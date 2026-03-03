from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv("PERPLEXITY_API_KEY"))
