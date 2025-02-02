from typing import List

from .ast import PrimitiveType, StructType, EnumType, SequenceType, ArrayType
from .Output import Output


class PythonOutput(Output):
    """Manages Output of Python Bindings

    Using a self nesting structure, a PythonOutput is created for each IDL
    module.
    """

    primitive_types = {  # (Python Type, Default Default Value)
        PrimitiveType.Kind.bool: ("bool", "False"),
        PrimitiveType.Kind.byte: ("int", "0"),
        PrimitiveType.Kind.u8: ("int", "0"),
        PrimitiveType.Kind.i8: ("int", "0"),
        PrimitiveType.Kind.u16: ("int", "0"),
        PrimitiveType.Kind.i16: ("int", "0"),
        PrimitiveType.Kind.u32: ("int", "0"),
        PrimitiveType.Kind.i32: ("int", "0"),
        PrimitiveType.Kind.u64: ("int", "0"),
        PrimitiveType.Kind.i64: ("int", "0"),
        PrimitiveType.Kind.f32: ("float", "0.0"),
        PrimitiveType.Kind.f64: ("float", "0.0"),
        PrimitiveType.Kind.c8: ("chr", "'\\x00'"),
        PrimitiveType.Kind.c16: ("str", "'\\x00'"),
        PrimitiveType.Kind.s8: ("str", "''"),
        PrimitiveType.Kind.s16: ("str", "''"),
    }

    def __init__(self, context: dict, name: str):
        self.submodules: List[PythonOutput] = []
        self.module = None
        new_context = context.copy()
        new_context.update(
            dict(
                output=context["output"] / name,
                types=[],
                has_struct=False,
                has_enum=False,
                has_sequence=False,
            )
        )
        super().__init__(
            new_context, new_context["output"], {"__init__.py": "user_py.tpl"}
        )

    def write(self):
        super().write()
        for submodule in self.submodules:
            submodule.write()

    def visit_root_module(self, root_module):
        self.module = root_module
        super().visit_module(root_module)

    def visit_module(self, module):
        submodule = PythonOutput(self.context, module.local_name())
        self.submodules.append(submodule)
        submodule.visit_root_module(module)

    def is_local_type(self, type_node):
        if isinstance(type_node, (SequenceType, ArrayType)):
            return type_node.base_type in self.module.types.values()
        else:
            return type_node in self.module.types.values()

    def get_python_type_string(self, field_type):
        if isinstance(field_type, SequenceType) and isinstance(field_type.base_type, PrimitiveType) \
                and field_type.base_type.kind.name in ["c8"]:
                return "memoryview"
        elif isinstance(field_type, PrimitiveType):
            return self.primitive_types[field_type.kind][0]
        else:
            return field_type.local_name()

    def get_python_default_value_string(self, field_type):
        if isinstance(field_type, PrimitiveType):
            return self.primitive_types[field_type.kind][1]
        else:
            type_name = self.get_python_type_string(field_type)
            if isinstance(field_type, StructType):
                return type_name + "()"
            elif isinstance(field_type, EnumType):
                return type_name + "." + field_type.default_member
            elif isinstance(field_type, SequenceType):
                if isinstance(field_type.base_type, PrimitiveType) and field_type.base_type.kind.name in ["c8"]:
                    return "memoryview(bytearray('', 'utf-8'))"
                else:
                    return "field(default_factory={type})".format(type=type_name)
            elif isinstance(field_type, ArrayType):
                return "field(default_factory=list)"
            else:
                raise NotImplementedError(repr(field_type) + " is not supported")

    def visit_struct(self, struct_type):
        self.context["has_struct"] = True
        d = dict(
                local_name=struct_type.local_name(),
                type_support=self.context["native_package_name"]
                if struct_type.is_topic_type
                else None,
                struct=dict(
                    fields=[
                        dict(
                            name=name,
                            type=self.get_python_type_string(node.type_node),
                            default_value=self.get_python_default_value_string(node.type_node),
                        )
                        for name, node in struct_type.fields.items()
                    ],
                ),
            )
        self.context["types"].append(d)

    def visit_enum(self, enum_type):
        self.context["has_enum"] = True
        self.context["types"].append(
            dict(
                local_name=enum_type.local_name(),
                enum=dict(
                    members=[
                        dict(name=name, value=value)
                        for name, value in enum_type.members.items()
                    ],
                ),
            )
        )

    def visit_sequence(self, sequence_type):
        self.context["has_sequence"] = True
        type = sequence_type.base_type.local_name()
        if type == None:
            type = self.primitive_types[sequence_type.base_type.kind][0]
        d = dict(
            local_name=sequence_type.local_name(),
            type_support=self.context["native_package_name"]
            if sequence_type.is_topic_type
            else None,
            sequence=dict(
                type=type,
                len=sequence_type.max_count,
            ),
        )
        self.context["types"].append(d)
