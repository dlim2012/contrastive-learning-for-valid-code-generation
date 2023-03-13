import libcst as cst
import libcst.matchers as m
from libcst.metadata import ParentNodeProvider

from preprocess.transform.utils.visit import has_new_line


def add_parenthesis_if_new_line(node):
    if has_new_line(node):
        if hasattr(node, "lpar"):
            return node.with_changes(lpar=[cst.LeftParen()], rpar=[cst.RightParen()])
        else:
            raise NotImplementedError()
    return node


def modify_local_variable_names(updated_node, updated_names):
    class ModifySingleVariableName(cst.CSTTransformer):
        METADATA_DEPENDENCIES = (ParentNodeProvider,)

        def __init__(self, updated_names):
            self.updated_names = updated_names

        def leave_Name(
                self, original_node: "Name", updated_node: "Name"
        ) -> "BaseExpression":
            parent = self.get_metadata(ParentNodeProvider, original_node)

            if m.matches(parent, m.Attribute()):
                if original_node == parent.attr:
                    return updated_node
            elif m.matches(parent, m.Arg()):
                if original_node == parent.keyword:
                    return updated_node

            if updated_node.value in self.updated_names:
                return updated_node.with_changes(value=self.updated_names[updated_node.value])
            return updated_node

    # Create a new module to use ParentNodeProvider
    module = cst.Module(body=(updated_node,))

    wrapper = cst.metadata.MetadataWrapper(module)
    transformer = ModifySingleVariableName(updated_names)
    updated_node = wrapper.visit(transformer)

    return updated_node.body[0]
