import libcst as cst
import libcst.matchers as m

from preprocess.transform.utils.modify_after_extraction import modify_after_extraction, ModifyAfterExtractionTransformer


def _lambda_to_function(target, value, name_generator):
    body = [
        cst.FunctionDef(
            name=target,
            params=value.params,
            body=cst.IndentedBlock(
                (cst.SimpleStatementLine((cst.Return(value.body),)),)
            )
        )
    ]
    return body


class LambdaToFunctionTransformer(ModifyAfterExtractionTransformer):
    def __init__(self, p=1):
        super().__init__([m.Lambda()], [m.Name()], _lambda_to_function, p=p)

    def get_logs(self):
        return {"lambda_to_function": self.num_changes}

def change_lambda_to_function(source, p=1):
    source_tree = cst.parse_module(source)
    fixed_module, num_changes = modify_after_extraction(source_tree, [m.Lambda()], [m.Name()], _lambda_to_function, p=p)
    return fixed_module.code, {'lambda_to_function': num_changes}


if __name__ == "__main__":
    source = '''
p = 0
a, f, b = 1, lambda x: func(x**2), 2

lambda z: z # expression
'''
    from preprocess.transform.utils.tools import transform, print_code_diff

    p = 1
    fixed, num_changes = transform(source, LambdaToFunctionTransformer, (p,))

    print_code_diff(source, fixed)
    cst.parse_module(fixed)
    print(num_changes)
