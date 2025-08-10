from setuptools import setup

setup(
    name="profile_summarizer_agent",
    version="0.1.0",
    description="Gemini-powered profile summarisation agent",
    python_requires=">=3.9",
    package_dir={"": "src"},
    py_modules=["profile_summarizer_agent"],
    install_requires=[
        "google-generativeai>=0.4,<1.0",
        "pydantic>=2.8,<3.0",
        "pyyaml>=6.0,<7.0",
        "tqdm>=4.66,<5.0",
        "python-dotenv>=1.0,<2.0",
    ],
)
