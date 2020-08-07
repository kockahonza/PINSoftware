import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PINSoftware", # Replace with your own username
    version="0.1",
    author="Jan Kocka",
    author_email="kockahonza@gmail.com",
    description="Software for the xPIN + Sample and Hold + NI-6002 setup at ELI Beamlines",
    url="https://github.com/kockahonza/PINSoftware",
    packages=setuptools.find_packages(),
    install_requires=[
        'dash',
        'dash-bootstrap-components',
        'waitress',
        'nidaqmx',
        'h5py',
        'matplotlib'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
