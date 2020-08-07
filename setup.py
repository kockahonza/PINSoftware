import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PINDiode-software", # Replace with your own username
    version="0.0.1",
    author="Jan Kocka",
    author_email="kockahonza@gmail.com",
    description="Software for the xPIN + Sample and Hold + NI-6002 setup at ELI Beamlines",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
