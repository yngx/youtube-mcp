# Python Development Notes

## Why virtual environments?
## Without venv: packages install globally (messy)
## With venv: each project has its own packages (clean)

## Common commands:
python -m venv venv # Create virtual evironment
source venv/bin/activate # Activate virtual environment
deactivate  # Exit the virtual environment
rm -rf venv  # Delete and start over if needed

## Pro tip: Add venv/ to .gitignore
echo "venv/" > .gitignore

## Requirements
pip freeze > requirements.txt

## Package Management Evolution for Python:
2015: pip + virtualenv
2017: pipenv (tried to be npm for Python)
2018: poetry (better, but complex)
2023: pip + venv (standard library!)
2024: uv (the new hotness)


# Language

Decorators