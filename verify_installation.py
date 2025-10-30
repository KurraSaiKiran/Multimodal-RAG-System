"""
Installation verification script
Run this to verify all dependencies are installed correctly
"""
import sys

def check_imports():
    """Check if all required packages can be imported"""
    packages = {
        'flask': 'Flask',
        'chromadb': 'ChromaDB',
        'PIL': 'Pillow',
        'torch': 'PyTorch',
        'transformers': 'Transformers',
        'sentence_transformers': 'Sentence Transformers',
        'PyPDF2': 'PyPDF2',
        'pdfplumber': 'pdfplumber',
        'pdf2image': 'pdf2image',
        'openai': 'OpenAI',
        'dotenv': 'python-dotenv',
        'diskcache': 'diskcache',
        'numpy': 'NumPy',
    }
    
    print("=" * 60)
    print("Checking Package Installations")
    print("=" * 60)
    
    all_good = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name:<25} installed")
        except ImportError:
            print(f"✗ {name:<25} NOT installed")
            all_good = False
    
    print("=" * 60)
    
    if all_good:
        print("✓ All packages installed successfully!")
    else:
        print("✗ Some packages are missing. Run: pip install -r requirements.txt")
    
    return all_good


def check_python_version():
    """Check Python version"""
    print("\nPython Version Check:")
    version = sys.version_info
    print(f"Current version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python version is compatible")
        return True
    else:
        print("✗ Python 3.9+ required")
        return False


def check_environment():
    """Check if .env file exists"""
    import os
    from pathlib import Path
    
    print("\nEnvironment Check:")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✓ .env file exists")
        
        # Check for required keys
        from dotenv import load_dotenv
        load_dotenv()
        
        grok_key = os.getenv('GROK_API_KEY')
        if grok_key and grok_key != 'your_grok_api_key_here':
            print("✓ GROK_API_KEY is configured")
            return True
        else:
            print("⚠ GROK_API_KEY not configured in .env")
            print("  The system will use local models as fallback")
            return True
    else:
        print("⚠ .env file not found")
        print("  Copy .env.example to .env and configure your API keys")
        return False


def check_directories():
    """Check if required directories exist"""
    from pathlib import Path
    
    print("\nDirectory Check:")
    dirs = ['uploads', 'logs', 'cache', 'chroma_db']
    
    for dir_name in dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"✓ {dir_name}/ directory exists")
        else:
            print(f"⚠ {dir_name}/ will be created on first run")
    
    return True


def main():
    """Run all checks"""
    print("\n🔍 Multimodal RAG System - Installation Verification\n")
    
    checks = [
        ("Python Version", check_python_version()),
        ("Package Installation", check_imports()),
        ("Environment Configuration", check_environment()),
        ("Directory Structure", check_directories()),
    ]
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = all(result for _, result in checks)
    
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All checks passed! You can run the application with:")
        print("  python app.py")
    else:
        print("\n⚠ Some checks failed. Please review the output above.")
        print("  Refer to README.md for detailed installation instructions.")
    
    print("\n")


if __name__ == "__main__":
    main()
