#include <cstdlib>
#include <string>
#include <vector>
#include <iostream>

#include <libfswatch/c++/path_utils.hpp>

int main() {
    std::vector<std::string> directory_children = fsw::get_directory_children(".");
    for (std::vector<std::string>::iterator it = directory_children.begin(); it != directory_children.end(); ++it) {
        std::cout << *it << std::endl;
    }

    return EXIT_SUCCESS;
}
