from setuptools import setup, Extension

module = Extension('render_funcs',
                    sources=['render_funcs.cpp'],
                    extra_compile_args=['-std=c++11'])

setup(
    name='render_funcs',
    version='1.0',
    ext_modules=[module]
)