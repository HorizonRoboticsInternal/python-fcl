import os
import sys

from Cython.Build import cythonize
from setuptools import Extension, setup, Command
from setuptools.command.install import install
from setuptools.command.build import build
from setuptools.command.develop import develop
import subprocess
import tempfile

INSTALL_PREFIX_WIN = "deps\\install"

PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))


def is_nix_platform(platform):
    for prefix in ["darwin", "linux", "bsd"]:
        if prefix in sys.platform:
            return True
    return False


def get_include_dirs():
    if is_nix_platform(sys.platform):
        include_dirs = [
            os.path.join(PACKAGE_ROOT, "include"),
            os.path.join(PACKAGE_ROOT, "include/eigen3"),
            "/usr/include",
            "/usr/local/include",
            "/usr/include/eigen3",
            "/usr/local/include/eigen3",
        ]

        if "CPATH" in os.environ:
            include_dirs += os.environ["CPATH"].split(":")

    elif sys.platform == "win32":
        include_dirs = [
            f"{INSTALL_PREFIX_WIN}\\include",
            f"{INSTALL_PREFIX_WIN}\\include\\eigen3",
        ]
    else:
        raise NotImplementedError(sys.platform)

    # get the numpy include path from numpy
    import numpy

    include_dirs.append(numpy.get_include())
    return include_dirs


def get_libraries_dir():
    if is_nix_platform(sys.platform):
        lib_dirs = [
            os.path.join(PACKAGE_ROOT, "lib"),
            "/usr/lib", "/usr/local/lib"]

        if "LD_LIBRARY_PATH" in os.environ:
            lib_dirs += os.environ["LD_LIBRARY_PATH"].split(":")
        return lib_dirs
    if sys.platform == "win32":
        return [f"{INSTALL_PREFIX_WIN}\\lib"]

    raise NotImplementedError(sys.platform)


def get_libraries():
    libraries = ["fcl", "octomap"]
    if sys.platform == "win32":
        libraries.extend(["octomath", "ccd", "vcruntime"])
    return libraries


class InstallDep(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self._install_eigen()
        self._install_libccd()
        self._install_octomap()
        self._install_fcl()

    def _install_eigen(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.check_call(
                "curl -OL https://gitlab.com/libeigen/eigen/-/archive/3.3.9/eigen-3.3.9.tar.gz; "
                "tar -zxf eigen-3.3.9.tar.gz; cd eigen-3.3.9; "
                f"cmake -DCMAKE_INSTALL_PREFIX:PATH={PACKAGE_ROOT} -B build; "
                "cmake --install build",
                cwd=d, shell=True)

    def _install_libccd(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.check_call(
                "git clone --depth 1 --branch v2.1 https://github.com/danfis/libccd.git; "
                "cd libccd; "
                f"cmake -DCMAKE_INSTALL_PREFIX:PATH={PACKAGE_ROOT} -DENABLE_DOUBLE_PRECISION=ON .; "
                "make install -j8",
                cwd=d, shell=True)

    def _install_octomap(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.check_call(
                "git clone --depth 1 --branch v1.9.8 https://github.com/OctoMap/octomap.git; "
                "cd octomap; "
                "cmake -DCMAKE_BUILD_TYPE=Release -D BUILD_OCTOVIS_SUBPROJECT=OFF -D BUILD_DYNAMICETD3D_SUBPROJECT=OFF "
                f"-DCMAKE_INSTALL_PREFIX:PATH={PACKAGE_ROOT} .; "
                "make install -j8",
                cwd=d, shell=True)

    def _install_fcl(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.check_call(
                "git clone --depth 1 --branch v0.7.0 https://github.com/ambi-robotics/fcl.git; "
                "cd fcl; "
                f"cmake -DCMAKE_INSTALL_PREFIX:PATH={PACKAGE_ROOT} .; "
                "make install -j8",
                cwd=d, shell=True)


class Install(install):
    def run(self):
        self.run_command('install_dep')
        super().run()


class Build(build):
    sub_commands = [
        ('install_dep', lambda self: True),
        ] + build.sub_commands


class Develop(develop):
    def run(self):
        self.run_command('install_dep')
        super().run()


setup(
    name='pyfcl',
    ext_modules=cythonize(
        [
            Extension(
                "fcl.fcl",
                ["src/fcl/fcl.pyx"],
                include_dirs=get_include_dirs(),
                library_dirs=get_libraries_dir(),
                libraries=get_libraries(),
                language="c++",
                extra_compile_args=["-std=c++11"],
            )
        ],
    ),
    cmdclass={'install': Install,
              'build': Build,
              'develop': Develop,
              'install_dep': InstallDep},
    package_data={
        'pyfcl': [
            os.path.join(PACKAGE_ROOT, 'include/*.h'),
            os.path.join(PACKAGE_ROOT, 'lib/*.so')
        ]
    },
    install_requires=[
        'setuptools==63.1.0'
    ]
)
