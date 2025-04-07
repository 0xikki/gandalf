from setuptools import setup, find_packages

setup(
    name="crypto-regulator-checker",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "pydantic-settings",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "pytest",
        "pytest-asyncio",
        "httpx",
        "structlog",
        "python-json-logger",
        "redis"
    ]
) 