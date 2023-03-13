from keyword import kwlist, softkwlist

import libcst as cst

from preprocess.transform.utils.visit import get_all_names


class NameGenerator:
    """
    Generates a new name that is not seen in both the source code and the builtin scope
    Can customize new names by modifying the self.new_name method
    """

    def __init__(self, source_tree, preserved: set = None, exclude_builtin=True):
        self.exclude_builtin = exclude_builtin
        # built-in functions, constants, exceptions, global variables, etc
        self.builtin_scope = cst.metadata.GlobalScope().parent

        # note: 'self' need not preserve its name
        self.keywords = set(kwlist) | set(softkwlist)
        self.preserved = preserved if preserved else set()

        self.used_names = get_all_names(source_tree) if source_tree else set()

        self.count = 0

    def is_name_preserved(self, name):
        return name in self.preserved

    def is_name_builtin(self, name):
        return name in self.keywords or self.builtin_scope.__contains__(name)

    def is_name_used(self, name):
        return name in self.used_names

    # def is_imported_attribute(self, name):
    #     return name in self.imported_attributes

    def new_name(self):
        """
        Function to generate new variable name
        :return: new name
        """
        name = "v" + str(self.count)
        self.count += 1
        while self.is_name_preserved(name) or self.is_name_used(name) or \
                (self.exclude_builtin and self.is_name_builtin(name)):
            name = "v" + str(self.count)
            self.count += 1
        self.used_names.add(name)
        return name
