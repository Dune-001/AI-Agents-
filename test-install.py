import sys
import pkg_resources

print(f"Python version: {sys.version}\n")

packages = [
    "langchain", "langchain-openai", "langgraph", "langchain-community",
    "fastapi", "uvicorn", "pydantic", "python-dotenv"
]

for package in packages:
    try:
        version = pkg_resources.get_distribution(package).version
        print(f"✓ {package}: {version}")
    except pkg_resources.DistributionNotFound:
        print(f"✗ {package}: NOT INSTALLED")