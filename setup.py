from setuptools import setup, find_packages

setup(
    name="vivita-finance",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "supabase",
        "pydantic",
        "python-dotenv",
        "reportlab",
        "anthropic",
        "mailjet-rest"
    ]
)
