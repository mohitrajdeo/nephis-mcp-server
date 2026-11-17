from setuptools import find_packages, setup

setup(
    name="nephis",
    version="1.0.4",
    description="NEPHIS: High-Throughput Isolated Execution Substrate & Zero-Copy Database Branching for AI Agents",
    author="Mohit Raj Deo",
    author_email="mohit@mohitrajdeo.in",
    url="https://nephis.theeducode.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "nephisctl=nephis.cli:main",
            "thanaton=thanaton.cli:main",
            "mnemon=mnemon.cli:main",
            "nephis-mcp=nephis.mcp:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
    ],
)
