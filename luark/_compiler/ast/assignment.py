from lark.ast_utils import Ast


class AssignStmt(Ast, Statement):
    def __init__(self, var_list, expr_list=None):
        self.var_list: list[VarType] = var_list
        self.expr_list: list[Expression] = expr_list

    def emit(self, state: _ProgramState):
        proto = state.proto

        # Cache variables used in dot/table accesses to
        # ensure the assignment does not affect them.
        temp_indices = []
        for var in self.var_list:
            if isinstance(var, Var):
                # A normal var only referes to a name
                # and thus doesn't need to be cached.
                continue
            elif isinstance(var, DotAccess):
                index = proto.new_temporary()
                temp_indices.append(index)
                evaluate_single(state, var.expression)
                proto.add_opcode(f"store_local {index}")
            elif isinstance(var, TableAccess):
                table_index = proto.new_temporary()
                evaluate_single(state, var.table)
                proto.add_opcode(f"store_local {table_index}")
                temp_indices.append(table_index)

                if not isinstance(var.key, ConstExpr):
                    key_index = proto.new_temporary()
                    evaluate_single(state, var.key)
                    proto.add_opcode(f"store_local {key_index}")
                    temp_indices.append(key_index)

            else:
                raise InternalCompilerError("Illegal assignment.")

        exprs = self.expr_list
        adjust_static(state, len(self.var_list), exprs)

        temp_index = len(temp_indices) - 1  # ensure we read the indices in reverse order
        for var in reversed(self.var_list):
            if isinstance(var, Var):
                state.assign(state, var.name)
            elif isinstance(var, DotAccess):
                local_index: int = temp_indices[temp_index]
                temp_index -= 1

                const_index: int = proto.get_const_index(var.name)
                proto.add_opcode(f"load_local {local_index}")
                proto.add_opcode(f"push_const {const_index}")
                proto.add_opcode("set_table")
            elif isinstance(var, TableAccess):
                if isinstance(var.key, ConstExpr):
                    evaluate_single(state, var.key)
                else:
                    key_index = temp_indices[temp_index]
                    temp_index -= 1
                    proto.add_opcode(f"load_local {key_index}")

                table_index = temp_indices[temp_index]
                temp_index -= 1
                proto.add_opcode(f"load_local {table_index}")
                proto.add_opcode("set_table")

        for index in temp_indices:
            proto.release_local(index)
