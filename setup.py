from distutils.core import setup
setup(
  name = 'chalice-shrubbery',
  py_modules = ['chalice_shrubbery_cli'],
  entry_points = {
    'console_scripts': ['chalice-shrubbery=chalice_shrubbery_cli:cli'],
  },
  install_requires=[
        'click'
    ],
  description = 'chalice-shrubbery is a command line tool simplying cloud formation deployments with aws chalice',
  version = '0.14.108',
  author = 'Mark Sweat',
  author_email = 'mark@surfkansas.com',
  url = 'https://github.com/surfkansas/chalice-shrubbery', 
  download_url = 'https://github.com/surfkansas/chalice-shrubbery/archive/0.14.108.tar.gz'
)