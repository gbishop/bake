from textx import metamodel_from_file

bake_meta = metamodel_from_file("bake.tx")

bake_model = bake_meta.model_from_file("try.bake")
