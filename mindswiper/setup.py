from setuptools import setup, find_packages

setup(name='mindswiper',
      version='0.1',
      packages=find_packages(),
      install_requires=['numpy', 'scipy', 'scikit-learn',  'joblib', 'requests', 'matplotlib', 'python-osc', 'pynder'])