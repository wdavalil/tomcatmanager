"""setuptools based setup for tomcatmanager

"""

from setuptools import setup, find_packages
from codecs import open
from os import path


# get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README'), encoding='utf-8') as f:
    long_description = f.read()

setup(
	name='tomcatmanager',
	version='0.1.0',

	description='interact with the Tomcat Manager web application from the command line',
	long_description=long_description,

	author='Kotfu',
	author_email='kotfu@kotfu.net',
	url='https://github.com/kotfu/tomcat-manager',
	license='MIT',

	classifiers=[
	'Development Status :: 5 - Production/Stable',
	'Environment :: Console',
	'Topic :: System :: Systems Administration',
	'Topic :: Utilities',
	'Intended Audience :: Developers',
	'Intended Audience :: System Administrators',
	'License :: OSI Approved :: MIT License',
	'Programming Language :: Python :: 3',
	'Programming Language :: Python :: 3 :: Only',
	],

	keywords='java tomcat command line manager',

	packages=find_packages(),

	#install_requires=['cmd2'],
	python_requires='>=3',

	# define the scripts that should be created on installation
	entry_points={
		'console_scripts': [
			'tomcat-manager=tomcatmanager.__main__:main',
		],
	},
)