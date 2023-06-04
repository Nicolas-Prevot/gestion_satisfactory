


class Main_Object:
    def __init__(self, name, building) -> None:
        self.building = building

    def is_building(self):
        return self.building


class Building(Main_Object):
    # base_power_use, overclock, get_net_power_use, input_num, output_num
    def __init__(self) -> None:
        super().__init__(building=True)


class Item(Main_Object):
    def __init__(self, solid, raw) -> None:
        super().__init__(building=False)
        self.raw = raw
        self.solid = solid
    
    def is_raw(self):
        return self.raw
    def is_solid(self):
        return self.solid


class Recipe():
    def __init__(self) -> None:
        pass
