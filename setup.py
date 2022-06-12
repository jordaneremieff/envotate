from setuptools import find_packages, setup


def get_long_description():
    return open("README.md", "r", encoding="utf8").read()


setup(
    name="envotate",
    version="0.0.1",
    packages=find_packages(),
    license="MIT",
    url="https://github.com/jordaneremieff/envotate",
    description="Settings management using environment variables and type annotations.",
    long_description=get_long_description(),
    python_requires=">=3.9",
    package_data={"envotate": ["py.typed"]},
    long_description_content_type="text/markdown",
    author="Jordan Eremieff",
    author_email="jordan@eremieff.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
