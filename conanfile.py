# -*- coding: utf-8 -*-
import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment


class FsWatchConan(ConanFile):
    name = "fswatch"
    version = "1.14.0"
    description = "A cross-platform file change monitor with multiple backends"
    topics = ("conan", "fswatch", "event-notifications", "change-monitor", "inotify", "kqueue")
    url = "https://github.com/bincrafters/conan-fswatch"
    homepage = "https://github.com/emcrisostomo/fswatch"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "GPL-3.0"
    exports = ["LICENSE.md"]
    exports_sources = ["0001-mingw.patch"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _autotools = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        sha256 = "44d5707adc0e46d901ba95a5dc35c5cc282bd6f331fcf9dbf9fad4af0ed5b29d"
        tools.get("{0}/releases/download/{1}/fswatch-{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                "--enable-shared={}".format("yes" if self.options.shared else "no"),
                "--enable-static={}".format("no" if self.options.shared else "yes")
            ]
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)

            autotools_vars = self._autotools.vars
            if self._is_mingw:
                autotools_vars["CFLAGS"] = "-DHAVE_WINDOWS"
                autotools_vars["CXXFLAGS"] = "-DHAVE_WINDOWS"
            self._autotools.configure(args=args, configure_dir=self._source_subfolder, vars=autotools_vars)
        return self._autotools

    def build(self):
        if self._is_mingw:
            tools.patch(base_path=self._source_subfolder, patch_file="0001-mingw.patch")
        autotools = self._configure_autotools()
        autotools.make()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        autotools = self._configure_autotools()
        autotools.install()
        for folder in ["share", "bin"]:
            tools.rmdir(os.path.join(self.package_folder, folder))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "m"])
