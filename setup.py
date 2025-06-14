from setuptools import setup, find_packages

setup(
    name="procman",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "PyQt5>=5.15.0",
        "click>=8.1.0",
        "pyyaml>=6.0.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "python-multipart>=0.0.6"
    ],
    entry_points={
        "console_scripts": [
            "procman=procman.__main__:cli"
        ]
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A distributed process management system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
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
    python_requires=">=3.7"
) 