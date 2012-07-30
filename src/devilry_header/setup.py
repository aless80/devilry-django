from setuptools import setup, find_packages


setup(name = 'devilry_header',
      description = 'The header displayed at the top of most Devilry views.',
      version = '1.0',
      license='BSD',
      author = 'Espen Angell Kristiansen',
      packages=find_packages(exclude=['ez_setup']),
      install_requires = ['setuptools', 'Django',
                          'devilry', 'devilry_theme',
                          'django_seleniumhelpers', 'django_extjs4',
                          'djangosenchatools', 'djangorestframework'],
      include_package_data=True,
      long_description = open('README.rst').read(),
      zip_safe=False,
      classifiers=[
                   'Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved',
                   'Operating System :: OS Independent',
                   'Programming Language :: JavaScript',
                   'Programming Language :: Python'
                  ]
)
