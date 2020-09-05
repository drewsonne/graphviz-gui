from setuptools import setup

setup(
    name='graphviz-viewer',
    version='1.0.0',
    packages=['graphviz_gui'],
    url='https://github.com/drewsonne/graphviz-gui',
    use_scm_version=True,
    setup_requires=[
        'setuptools_scm',
        'setuptools_scm_git_archive'
    ],
    license='LGPLv2',
    author='Drew J. Sonne',
    author_email='drew.sonne@gmail.com',
    description='',
    entry_points={
        'console_scripts': ['graphviz-gui=graphviz_gui.main:main']
    },
    install_requires=["PyQt5==5.9.2",
"pydot",
"pyinstaller",
"click"
]

)
