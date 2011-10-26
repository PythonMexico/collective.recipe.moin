from setuptools import setup, find_packages
import os

version = '0.7'

tests_require = ['zope.testing', 'zc.buildout']

setup(name='collective.recipe.moin',
      version=version,
      description="A recipe to build a wiki site with MoinMoin",
      long_description=open("README.rst").read() + "\n" +
                       open("HISTORY.txt").read(),
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
          'zc.buildout',
          'zc.recipe.egg',
      ],
      entry_points="""
      [zc.buildout]
      default = collective.recipe.moin:Recipe
      """,

      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite='collective.recipe.moin.tests.test_docs.test_suite',
      )
