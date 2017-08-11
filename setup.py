from setuptools import setup, find_packages

install_requires = ["SQLAlchemy==1.1.9"]

setup(
    author="Grahame Bowland",
    author_email="grahame@angrygoats.net",
    description="EAlGIS data schema",
    long_description="EAlGIS data schema",
    license="GPL3",
    keywords="ealgis",
    url="https://github.com/ealgis/ealgis-data-schema",
    name="ealgis_data_schema",
    version="1.0.0",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=install_requires,
)
