from setuptools import setup, find_packages

setup(
    name="tralvisualizer",
    author="Spencer Bliven",
    author_email="spencer.bliven@gmail.com",
    url="https://github.com/acg-team/tral-visualization",
    license="GPL 2.0",
    version="1.0.0",
    #packages=find_packages(),
    py_modules=["repeatdiagram"],
    install_requires=[
        'biopython >= 1.72',  # needs #1622
        'reportlab >= 3.5',
    ],
    extras_require={
        'jupyter': ['ipython']
    }
)

