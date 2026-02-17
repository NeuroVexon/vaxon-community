from setuptools import setup

setup(
    name="axon-cli",
    version="1.0.0",
    py_modules=["axon_cli"],
    install_requires=[
        "typer>=0.9.0",
        "httpx>=0.27.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "axon=axon_cli:app",
        ],
    },
    python_requires=">=3.10",
    author="NeuroVexon",
    description="Axon CLI — Terminal-Steuerung fuer Axon by NeuroVexon",
)
