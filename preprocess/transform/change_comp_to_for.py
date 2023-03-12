"""
Dealing with nested comprehensions of list, set, and dictionary
"""

import libcst as cst
import libcst.matchers as m

from preprocess.transform.utils.create_node import create_expr_statement, create_subscr_assignment, \
    create_assign_statement
from preprocess.transform.utils.modify_after_extraction import modify_after_extraction, ModifyAfterExtractionTransformer
from preprocess.transform.utils.transform_node import add_parenthesis_if_new_line


def _stop_elt_loop(comp_node):
    if not hasattr(comp_node, "elt"):
        return True
    if m.matches(comp_node.elt, m.ListComp()):
        return False
    if m.matches(comp_node.elt, m.SetComp()):
        return False
    if m.matches(comp_node.elt, m.DictComp()):
        return False
    return True


def _for_loops(target, value, new_body):
    if value.inner_for_in:
        new_body = _for_loops(add_parenthesis_if_new_line(target), value.inner_for_in, new_body)

    for comp_if in reversed(value.ifs):
        new_body = (cst.If(
            add_parenthesis_if_new_line(comp_if.test),
            cst.IndentedBlock(new_body)
        ),)

    new_body = (cst.For(
        add_parenthesis_if_new_line(value.target),
        add_parenthesis_if_new_line(value.iter),
        cst.IndentedBlock(new_body)
    ),)
    return new_body


def _elt_to_body(target, comp_node, name_generator):
    if _stop_elt_loop(comp_node):
        if m.matches(comp_node, m.ListComp()):
            return (create_expr_statement(target, comp_node.elt, cst.Name("append")),)
        elif m.matches(comp_node, m.SetComp()):
            return (create_expr_statement(target, comp_node.elt, cst.Name("add")),)
        else:
            return (create_subscr_assignment(target, comp_node.value, comp_node.key),)

    new_var = cst.Name(name_generator.new_name())
    new_body = _elt_to_body(new_var, comp_node.elt, name_generator)

    if m.matches(comp_node.elt, m.ListComp()):
        new_structure = cst.List([])
        assign_statement = create_assign_statement(new_var, new_structure)
    elif m.matches(comp_node.elt, m.SetComp()):
        new_structure = cst.Call(cst.Name("set"))
        assign_statement = create_assign_statement(new_var, new_structure)
    else:
        new_structure = cst.Dict([])
        assign_statement = create_assign_statement(new_var, new_structure)

    for_statement = _for_loops(comp_node.elt.for_in.target, comp_node.elt.for_in, new_body)[0]

    if m.matches(comp_node, m.ListComp()):
        append_statement = create_expr_statement(target, new_var, cst.Name("append"))
    elif m.matches(comp_node, m.SetComp()):
        append_statement = create_expr_statement(target, new_var, cst.Name("add"))
    else:
        append_statement = create_expr_statement(target, new_var, cst.Name("add"))

    return (assign_statement, for_statement, append_statement,)


def _comp_to_for_loops(target, value, name_generator):
    new_body = _elt_to_body(target, value, name_generator)

    if m.matches(value, m.ListComp()):
        assign_value = cst.List([])
    elif m.matches(value, m.SetComp()):
        assign_value = cst.Call(cst.Name("set"))
    elif m.matches(value, m.DictComp()):
        assign_value = cst.Dict([])
    else:
        raise ValueError()

    assign_statement = cst.SimpleStatementLine(
        (
            cst.Assign(
                targets=(
                    cst.AssignTarget(target),
                ),
                value=assign_value
            ),
        )
    )

    for_statement = _for_loops(target, value.for_in, new_body)[0]

    return (assign_statement, for_statement,)


class ChangeCompToForTransformer(ModifyAfterExtractionTransformer):
    def __init__(self, comp_type, name_generator, p=1):
        value_types = {"list": [m.ListComp()], "set": [m.SetComp()], "dict": [m.DictComp()]}[comp_type]
        target_types = [m.Name(), m.Attribute()]
        super().__init__(value_types, target_types, _comp_to_for_loops, name_generator, p=p)
        self.comp_type = comp_type

    def get_logs(self):
        return {"comp_" + self.comp_type + "_to_for": self.num_changes}


if __name__ == "__main__":
    source = '''
def func(a):
    q = 1; a, b, c = 1, 2, [i if i == 1 else 0 for k in range(6) if k % 2 if k % 3 for j in range(6) if j % 2 for i in range(6) if i % 2]; q = 2
    
    p, q = {x: y for x, y in arr}, {x for x, y,
     z in [x, y,
     z]
     }
    
    p = [{key: value for key, value in d.items()} for d in dd]
    return a
'''
    source = '''
def consume(v0, v1, msg):

    """
    Consumer for this (CaptureData) class. Gets the data sent from yieldMetricsValue and
    sends it to the storage backends.
    """


    v2 ,builder_info = msg['build_data'], yield v0.v3.v4.get(("builders", v2['builderid' ]))

    if  v0._builder_name_matches( builder_info) and v0 .v5 == msg['data_name']:
        try:
            ret_val = v0._callback(msg['post_data'])

        except Exception as e:

            raise v6("CaptureData failed for build %s of builder %s."

                                       " Exception generated: %s with message %s"
                                       % (v2[ 'number'], builder_info ['name' ],

                                          type(e).__name__, str (e),))

        post_data  = ret_val
        series_name = '%s-%s' % (builder_info['name'], v0.v5)
        context = v0.v7(v2, builder_info['name']) 

        yield v0.v8(post_data, series_name, context)
    '''
    from preprocess.transform.utils.tools import transform, print_code_diff
    from preprocess.transform.utils.new_names import NameGenerator

    try:
        source_tree = cst.parse_module(source)
    except:
        raise ValueError("Source code could not be parsed")
    log = {}

    name_generator = NameGenerator(source_tree, set())
    p = 1
    for comp_type in ["list", "set", "dict"]:
        fixed, num_changes = transform(source, ChangeCompToForTransformer, (comp_type, name_generator, p))
        print(num_changes)
        print_code_diff(source, fixed)
        cst.parse_module(fixed)
        log.update(num_changes)
        source = fixed
    print(log)
