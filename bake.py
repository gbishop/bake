from textx import metamodel_from_file


class bake:
    def __init__(self):
        self.meta = metamodel_from_file("bake.tx")
        self.meta.register_obj_processors(
            {
                "Value": self.handleValue,
                "NamedValue": self.handleNamedValue,
                "PartName": self.handlePartName,
            }
        )

    def compile(self, name):
        print("compiling", name)
        self.model = self.meta.model_from_file(name)

    def handleProduct(self, v):
        value = v.value

    def handleValue(self, v):
        if v.named:
            v.value = v.named.value
        print("value", v.value)

    def handleNamedValue(self, v):
        if v.ingredient:
            v.value = v.part + "." + v.ingredient
        else:
            v.value = self.partName + "." + v.part

    def handlePartName(self, v):
        self.partName = v.name
        print("partName", v.name)

    def handlePart(self, v):
        print("part")


Baker = bake()
Baker.compile("try.bake")
