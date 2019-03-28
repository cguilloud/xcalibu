import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="xcalibu",
    version="0.9.0",
    description="Calibration library",
    long_description=long_description,
    url="https://gitlab.esrf.fr/bliss/xcalibu",
    author="Cyril Guilloud (ESRF-BCU)",
    author_email="prenom.name@truc.fr",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

