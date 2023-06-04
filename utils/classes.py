


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

['/wiki/Adaptive_Control_Unit', '/wiki/AI_Limiter', '/wiki/Alclad_Aluminum_Sheet', '/wiki/Alien_DNA_Capsule', '/wiki/Alien_Protein', '/wiki/Aluminum_Casing',
'/wiki/Aluminum_Ingot', '/wiki/Aluminum_Scrap', '/wiki/Assembly_Director_System', '/wiki/Automated_Wiring', '/wiki/Bacon_Agaric', '/wiki/Battery', '/wiki/Bauxite',
'/wiki/Beacon', '/wiki/Beryl_Nut', '/wiki/Biomass', '/wiki/Black_Powder', '/wiki/Blade_Runners', '/wiki/Boom_Box', '/wiki/Cable', '/wiki/Caterium_Ingot', '/wiki/Caterium_Ore',
'/wiki/Circuit_Board', '/wiki/Coal', '/wiki/Color_Cartridge', '/wiki/Color_Gun', '/wiki/Compacted_Coal', '/wiki/Computer', '/wiki/Concrete', '/wiki/Cooling_System',
'/wiki/Copper_Ingot', '/wiki/Copper_Ore', '/wiki/Copper_Powder', '/wiki/Copper_Sheet', '/wiki/Crude_Oil', '/wiki/Crystal_Oscillator', '/wiki/Electromagnetic_Control_Rod',
'/wiki/Empty_Canister', '/wiki/Empty_Fluid_Tank', '/wiki/Encased_Industrial_Beam', '/wiki/Encased_Plutonium_Cell', '/wiki/Encased_Uranium_Cell', '/wiki/Fabric',
'/wiki/Flower_Petals', '/wiki/Fused_Modular_Frame', '/wiki/Gas_Mask', '/wiki/Hazmat_Suit', '/wiki/Heat_Sink', '/wiki/Heavy_Modular_Frame', '/wiki/High-Speed_Connector',
'/wiki/Hover_Pack', '/wiki/Iron_Ingot', '/wiki/Iron_Ore', '/wiki/Iron_Plate', '/wiki/Iron_Rod', '/wiki/Jetpack', '/wiki/Leaves', '/wiki/Limestone',
'/wiki/Magnetic_Field_Generator', '/wiki/Medicinal_Inhaler', '/wiki/Modular_Engine', '/wiki/Modular_Frame', '/wiki/Motor', '/wiki/Mycelia', '/wiki/Nobelisk_Detonator',
'/wiki/Non-fissile_Uranium', '/wiki/Nuclear_Pasta', '/wiki/Object_Scanner', '/wiki/Packaged_Alumina_Solution', '/wiki/Packaged_Fuel', '/wiki/Packaged_Heavy_Oil_Residue',
'/wiki/Packaged_Liquid_Biofuel', '/wiki/Packaged_Nitric_Acid', '/wiki/Packaged_Nitrogen_Gas', '/wiki/Packaged_Oil', '/wiki/Packaged_Sulfuric_Acid',
'/wiki/Packaged_Turbofuel', '/wiki/Packaged_Water', '/wiki/Paleberry', '/wiki/Parachute', '/wiki/Petroleum_Coke', '/wiki/Plastic', '/wiki/Plutonium_Fuel_Rod',
'/wiki/Plutonium_Pellet', '/wiki/Plutonium_Waste', '/wiki/Polymer_Resin', '/wiki/Power_Shard', '/wiki/Power_Slug', '/wiki/Pressure_Conversion_Cube', '/wiki/Quartz_Crystal',
'/wiki/Quickwire', '/wiki/Radio_Control_Unit', '/wiki/Raw_Quartz', '/wiki/Rebar_Gun', '/wiki/Reinforced_Iron_Plate', '/wiki/Rifle', '/wiki/Rotor', '/wiki/Rubber',
'/wiki/SAM_Ore', '/wiki/Screw', '/wiki/Silica', '/wiki/Smart_Plating', '/wiki/Smokeless_Powder', '/wiki/Solid_Biofuel', '/wiki/Stator', '/wiki/Steel_Beam', '/wiki/Steel_Ingot',
'/wiki/Steel_Pipe', '/wiki/Sulfur', '/wiki/Supercomputer', '/wiki/Thermal_Propulsion_Rocket', '/wiki/Turbo_Motor', '/wiki/Turbofuel', '/wiki/Uranium', '/wiki/Uranium_Fuel_Rod',
'/wiki/Uranium_Waste', '/wiki/Versatile_Framework', '/wiki/Wire', '/wiki/Wood', '/wiki/Xeno-Basher', '/wiki/Xeno-Zapper', '/wiki/Zipline', '/wiki/Fuel', '/wiki/Turbofuel',
'/wiki/Nitric_Acid', '/wiki/Nitrogen_Gas', '/wiki/Sulfuric_Acid', '/wiki/Liquid_Biofuel', '/wiki/Alumina_Solution', '/wiki/Heavy_Oil_Residue']