import setuptools


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


install_reqs = parse_requirements('requirements.txt')

setuptools.setup(
    name="sberpm",
    version="1.0.1",
    author="Sber Process Mining R&D Team",
    author_email='Smetanev.d.m@sberbank.ru',
    description="Python Library for Process Mining",
    url="https://github.com/SberProcessMining/Sber_Process_Mining",
    include_package_data=True,
    packages=['sberpm',
              'sberpm.autoinsights',
              'sberpm.bpmn', 'sberpm.bpmn._bpmn_graph_to_file',
              'sberpm.metrics',
              'sberpm.miners',
              'sberpm.ml', 'sberpm.ml.processes', 'sberpm.ml.vectorizer',
              'sberpm.visual'
              ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    install_requires=install_reqs
)
