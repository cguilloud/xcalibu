import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="calibu",
    version="0.9.0",
    description="Calibration library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.esrf.fr/bliss/xcalibu",
    author="Cyril Guilloud (ESRF-BCU)",
    author_email="prenom.name@truc.fr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

