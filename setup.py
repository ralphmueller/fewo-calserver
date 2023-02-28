from setuptools import find_packages, setup

setup(
    name='rneu v2',
    author='Ralph Mueller',
    version='1.2',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'flask-wtf',
        'flask_cors',
        'email-validator',
        'babel',
        'flask-assets',
        'python-dotenv',
        'cssmin',
        'jsmin'
    ],
)
