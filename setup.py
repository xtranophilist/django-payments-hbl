from setuptools import setup

setup(name='django-payments-hbl',
      version='0.1.1',
      description='Himalayan Bank Payment Gateway with django-payments',
      url='http://github.com/xtranophilist/django-payments-hbl',
      author='Dipesh Acharya',
      author_email='dipesh@awecode.com',
      maintainer='Awecode',
      license='BSD License',
      packages=['django_payments_hbl'],
      long_description=open('README.md').read(),
      include_package_data=True,
      zip_safe=False,
      keywords='django,payments,ecommerce,saleor,bank',
      classifiers=[
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries :: Application Frameworks',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ],
      )
