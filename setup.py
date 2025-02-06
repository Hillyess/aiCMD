from setuptools import setup, find_packages

def read_file(filename):
    """读取文件内容"""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

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
            'ai=aicmd.run:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered command-line assistant",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/aicmd",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 