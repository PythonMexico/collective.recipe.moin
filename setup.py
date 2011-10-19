from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='collective.recipe.moin',
      version=version,
      description="A recipe to build a wiki site with MoinMoin",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Buildout",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        ],
      keywords='',
      author='Erik Rivera',
      author_email='erik@rivera.pro',
      url='https://github.com/pythonmexico/collective.recipe.moin',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', 'collective.recipe'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'setuptools',
          'zc.recipe.egg',
      ],
      entry_points="""
      [zc.buildout]
      default = collective.recipe.moin:Recipe
      """,
      )
