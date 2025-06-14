from setuptools import setup, find_packages

setup(
    name="procman",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "requests>=2.26.0",
        "psutil>=5.8.0",
        "PyQt5>=5.15.0",
        "click>=8.0.0",
        "rich>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "procman-sheriff=procman.sheriff.gui:main",
            "procman-sheriff-cli=procman.sheriff.cli:main",
            "procman-deputy=procman.deputy.__main__:main",
        ],
    },
    python_requires=">=3.7",
    description="A distributed process manager with GUI and CLI interfaces",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/procman",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown"
) 