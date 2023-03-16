__version__ = "0.1.0"

from setuptools import find_namespace_packages, setup

setup(
    name="grafana-k8-sidecar",
    author="Graeme Davidson",
    author_email="graedavidson@gmail.com",
    description="Kubernetes sidecar installed alongside Grafana to deploy dashboards.",
    url="https://github.com/graemedavidson/grafana-k8-sidecar",
    setup_requires=["setuptools_scm"],
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    include_package_data=True,
    version=__version__,
    install_requires=[
        "click >= 8.1",
        "prometheus_client >= 0.16",
        "kopf >= 1.36.0",
        "kubernetes >= 26.1.0",
    ],
    extras_require={
        "dev": [
            "pytest >= 7.2",
            "pytest-mock >= 3.10",
            "flake8 >= 6.0",
            "coverage >= 7.2",
            "requests-mock >= 1.10",
            "testfixtures >= 7.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "grafana-k8-sidecar=sidecar.sidecar:scan",
        ],
    },
    python_requires=">3.10",
)
