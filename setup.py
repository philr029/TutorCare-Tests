from setuptools import setup, find_packages

setup(
    name="security-toolkit",
    version="1.0.0",
    description="Modular security diagnostic toolkit for IP reputation, phone validation, and website health checks",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "dnspython>=2.4.0",
        "phonenumbers>=8.13.0",
        "cryptography>=41.0.0",
        "flask>=3.0.0",
        "click>=8.1.0",
        "pyyaml>=6.0.1",
    ],
    entry_points={
        "console_scripts": [
            "security-toolkit=security_toolkit.cli:cli",
        ],
    },
    python_requires=">=3.9",
)
