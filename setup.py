from setuptools import setup, find_packages

def read_requirements(filename):
    """读取依赖文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="aicmd",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "prompt_toolkit>=3.0.0",
        "requests>=2.25.1",
        "colorama>=0.4.4",
    ],
    entry_points={
        'console_scripts': [
            'ai=run:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered command-line assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/aicmd",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 