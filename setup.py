from setuptools import setup

setup(
    name='graphviz-viewer',
    version='1.0.0',
    packages=['graphviz_gui'],
    url='',
    license='LGPLv2',
    author='drews',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'graphviz-gui=graphviz_gui.main:main'
        ]
    }
)
