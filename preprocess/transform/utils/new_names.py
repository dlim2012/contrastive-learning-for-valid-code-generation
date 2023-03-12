from keyword import kwlist, softkwlist

import libcst as cst

from preprocess.transform.utils.visit import get_all_names


class NameGenerator:
    """
    Generates a new name that is not seen in both the source code and the builtin scope
    Can customize new names by modifying the self.new_name method
    """

    def __init__(self, source_tree, preserved: set, exclude_builtin=True):

        self.exclude_builtin = exclude_builtin
        # built-in functions, constants, exceptions, global variables, etc
        self.builtin_scope = cst.metadata.GlobalScope().parent

        # note: 'self' need not preserve its name
        self.preserved = preserved | set(kwlist) | set(softkwlist)

        if source_tree:
            self.preserved = self.preserved.union(get_all_names(source_tree))
        self.count = 0

    def is_name_preserved(self, name):
        return name in self.preserved or \
               (self.exclude_builtin and self.builtin_scope.__contains__(name))

    def new_name(self, reference=None):
        """
        Function to generate new variable name
        :return: new name
        """
        name = "v" + str(self.count)
        self.count += 1
        while self.is_name_preserved(name):
            name = "v" + str(self.count)
            self.count += 1
        self.preserved.add(name)
        return name
