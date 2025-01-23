from setuptools import setup, find_packages

setup(
    name="iiif_htr",
    version="0.0.1",
    packages=find_packages(),
    author="William J. B. Mattingly",
    description="A Python package for working with IIIF manifests and LLMs for HTR",
    install_requires=[
        "Pillow",
        "google-auth",
        "openai",
        "vertexai",
    ],
)
