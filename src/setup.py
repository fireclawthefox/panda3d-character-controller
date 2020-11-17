import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="panda3d-character-controller",
    version="20.11",
    author="Fireclaw",
    author_email="fireclawthefox@gmail.com",
    description="Extensive character control system to be used with the Panda3D engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fireclawthefox/panda3d-character-controller",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
    ],
    install_requires=[
        'panda3d',
    ],
    python_requires='>=3.6',
)
