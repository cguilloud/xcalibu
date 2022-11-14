import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="xcalibu",
    version="0.9.5",
    description="Calibration library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cguilloud/xcalibu",
    author="Cyril Guilloud (ESRF-BCU)",
    author_email="prenom.name@truc.fr",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "xcalibu = xcalibu.xcalibu:main",
            "xcalibu_server = xcalibu.Xcalibuds:main",
        ]
    },
)
