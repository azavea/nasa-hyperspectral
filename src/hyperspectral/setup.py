from setuptools import setup, find_packages

setup(
    name='hyperspectral',
    version='0.0.1',
    description='Hyperspectral imaging and processing utilities',
    packages=find_packages(),
    python_requires='>=3.6',
    package_data={'hyperspectral.resources': ['hyperspectral/resources/prefixed_double_filter.mat']},
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'parsec'
    ],
)
