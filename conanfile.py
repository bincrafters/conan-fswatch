import os
import shutil
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.tools import Version
from conans.errors import ConanInvalidConfiguration


class FsWatchConan(ConanFile):
    name = "fswatch"
    version = "1.14.0"
    description = "A cross-platform file change monitor with multiple backends"
    topics = ("conan", "fswatch", "event-notifications", "change-monitor", "inotify", "kqueue")
    url = "https://github.com/bincrafters/conan-fswatch"
    homepage = "https://github.com/emcrisostomo/fswatch"
    license = "GPL-3.0"
    exports_sources = ["0001-mingw.patch", "libfswatch_config-msvc.h", "CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _autotools = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _source_subfolder_unix(self):
        return "source_subfolder_unix"

    @property
    def _is_clang_i386(self):
        return self.settings.compiler == "clang" and self.settings.arch == "x86"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.os == "Windows" and \
           self.settings.compiler == "Visual Studio" and \
           Version(self.settings.compiler.version.value) < "14":
            raise ConanInvalidConfiguration("fswatch requires Visual Studio >= 14")

    def requirements(self):
        if self.settings.compiler == "Visual Studio" and self.settings.os == "Windows":
            self.requires("dirent/1.23.2")

    def source(self):
        sha256 = "44d5707adc0e46d901ba95a5dc35c5cc282bd6f331fcf9dbf9fad4af0ed5b29d"
        tools.get("{0}/releases/download/{1}/fswatch-{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder_unix)

        sha256 = "c4f5ef92e79dda7e50c1ded42784791ef536c99684f3d677f6621fe73ee857d2"
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                "--enable-shared={}".format("yes" if self.options.shared else "no"),
                "--enable-static={}".format("no" if self.options.shared else "yes")
            ]
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)

            autotools_vars = self._autotools.vars
            if self._is_clang_i386:
                autotools_vars["LIBS"] = "-latomic"
            self._autotools.configure(args=args, configure_dir=self._source_subfolder_unix, vars=autotools_vars)
        return self._autotools

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.verbose = True
        if self.settings.os == 'Windows' and self.settings.compiler == 'Visual Studio':
            cmake.definitions['CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS'] = self.options.shared
        cmake.configure()
        return cmake

    def _build_windows(self):
        tools.patch(base_path=self._source_subfolder, patch_file="0001-mingw.patch")
        shutil.move("libfswatch_config-msvc.h", os.path.join(self._source_subfolder, "libfswatch_config.h"))
        cmake = self._configure_cmake()
        cmake.build()

    def _build_unix(self):
        autotools = self._configure_autotools()
        autotools.make()

    def build(self):
        if self.settings.os == "Windows":
            self._build_windows()
        else:
            self._build_unix()

    def _package_unix(self):
        autotools = self._configure_autotools()
        autotools.install()
        for folder in ["share", "bin"]:
            tools.rmdir(os.path.join(self.package_folder, folder))

    def _package_windows(self):
        cmake = self._configure_cmake()
        cmake.install()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        if self.settings.os == "Windows":
            self._package_windows()
        else:
            self._package_unix()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "m"])
        if self._is_clang_i386:
            self.cpp_info.libs.append("atomic")
        if self.settings.os in ["Macos", "iOS", "watchOS", "tvOS"]:
            self.cpp_info.exelinkflags.extend(["-framework CoreFoundation", "-framework CoreServices"])
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
