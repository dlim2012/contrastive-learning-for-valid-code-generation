import libcst as cst
import libcst.matchers as m
from libcst import MaybeSentinel


def create_expr_statement(target, value, attr):
    expr_statement = cst.SimpleStatementLine((
        cst.Expr(
            cst.Call(
                cst.Attribute(
                    target.deep_clone(), attr, cst.Dot()),
                (
                    cst.Arg(
                        value.deep_clone()
                    ),
                )
            )
        )
        ,))
    return expr_statement


def create_subscr_assignment(target, value, key):
    subscr_assignment = cst.SimpleStatementLine((
        cst.Assign(
            targets=(cst.AssignTarget(cst.Subscript(
                target.deep_clone(), (cst.SubscriptElement(cst.Index(key.deep_clone())),)
            )),),
            value=value.deep_clone()
        )
        ,))
    return subscr_assignment


def create_assign_statement(target, value, leading_lines=()):
    assign_assignment = cst.SimpleStatementLine(
        (
            cst.Assign(
                targets=(
                    cst.AssignTarget(target.deep_clone()),
                ),
                value=value.deep_clone()
            ),
        ),
        leading_lines=leading_lines
    )
    return assign_assignment

def create_assign_plural(targets, values):
    def hasParenthesizedWhitespace(elements):
        for element in elements:
            if m.matches(element.comma, m.Comma()):
                if m.matches(element.comma.whitespace_before, m.ParenthesizedWhitespace()):
                    return True
                if m.matches(element.comma.whitespace_after, m.ParenthesizedWhitespace()):
                    return True
        return False

    assert len(targets) > 0

    # remove last comma
    targets = [target.deep_clone() for target in targets]
    targets[-1] = targets[-1].with_changes(comma=MaybeSentinel.DEFAULT)
    values = [value.deep_clone() for value in values]
    values[-1] = values[-1].with_changes(comma=MaybeSentinel.DEFAULT)

    target_parenthesis = hasParenthesizedWhitespace(targets)
    value_parenthesis = hasParenthesizedWhitespace(values)


    assign = cst.Assign(
        targets=(
            cst.AssignTarget(
                cst.Tuple(
                    elements=targets,
                ).with_changes(
                    lpar=[cst.LeftParen()] if target_parenthesis else [],
                    rpar=[cst.RightParen()] if target_parenthesis else []
                ) if len(targets) > 1 else targets[0]
            ),
        ),
        value=cst.Tuple(
            elements=values,
        ).with_changes(
            lpar=[cst.LeftParen()] if value_parenthesis else [],
            rpar=[cst.RightParen()] if value_parenthesis else []
        ) if len(values) > 1 else values[0],

    )
    return assign

def create_assign_statement_plural(targets, values, leading_lines=()):
    assign = create_assign_plural(targets, values)

    assign_statement = cst.SimpleStatementLine(
        body=(assign,),
        leading_lines=leading_lines
    )
    return assign_statement


def create_add_statement(target, step_value: cst.BaseExpression = None):
    aug_statement_line = cst.SimpleStatementLine(
        body=[cst.AugAssign(
            target=target.deep_clone(),
            operator=cst.AddAssign(),
            value=step_value.deep_clone() if step_value else cst.Integer("1")
        )]
    )
    return aug_statement_line
