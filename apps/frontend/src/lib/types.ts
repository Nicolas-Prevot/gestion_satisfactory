export type Scenario = {
  id: number;
  name: string;
  is_deleted: boolean;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Area = {
  id: number;
  scenario_id: number;
  name: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type Factory = {
  id: number;
  scenario_id: number;
  area_id: number;
  name: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type Item = {
  id: number;
  name: string;
  image_url: string | null;
  image_url_remote: string | null;
};

export type Building = {
  id: number;
  name: string;
  group: string | null;
  subgroup: string | null;
  tier: number;
  power_usage: number | null;
  min_consumption: number | null;
  max_consumption: number | null;
  image_url: string | null;
  image_url_remote: string | null;
};

export type Recipe = {
  id: number;
  building_name: string;
  recipe_name: string;
  recipe_alternate: boolean;
  duration: number;
  unlocked_by: string | null;
  tier: number;
  min_consumption: number | null;
  max_consumption: number | null;
  ingredient_1: string | null;
  ingredient_amount_1: number | null;
  ingredient_2: string | null;
  ingredient_amount_2: number | null;
  ingredient_3: string | null;
  ingredient_amount_3: number | null;
  ingredient_4: string | null;
  ingredient_amount_4: number | null;
  product_1: string | null;
  product_amount_1: number | null;
  product_2: string | null;
  product_amount_2: number | null;
};

export type Line = {
  id: number;
  scenario_id: number;
  area_id: number;
  factory_id: number | null;
  name: string;
  recipe_id: number;
  recipe_name: string;
  building_name: string;
  building_count: number;
  efficiency_multiplier: string;
  version: number;
};

export type RateItem = {
  item_name: string;
  net_rate: string;
  produced_rate: string;
  consumed_rate: string;
  image_url: string | null;
};

export type Balance = {
  scope: "scenario" | "area" | "factory";
  scope_id: number;
  power_mw: string;
  outputs: RateItem[];
  inputs: RateItem[];
  intermediates: RateItem[];
};

export type ConflictResponse = {
  error: "conflict";
  entity: "line";
  server: Record<string, unknown>;
  client: Record<string, unknown>;
  conflicting_fields: string[];
};

export type OptimizerSelection = {
  item_name: string;
  quantity: string;
};

export type OptimizerRequest = {
  max_tier: number;
  selected_products: OptimizerSelection[];
  available_items: Record<string, string>;
  raw_weights: Record<string, string>;
  raw_limits: Record<string, string>;
};

export type OptimizerResult = {
  status: string;
  recipes: {
    recipe_id: number;
    recipe_name: string;
    building_name: string;
    building_image_url: string | null;
    nb_building: string;
    efficiency_multiplier: string;
    outputs: {
      item_name: string;
      rate: string;
      per_building_rate: string;
      total_rate: string;
      image_url: string | null;
    }[];
    inputs: {
      item_name: string;
      rate: string;
      per_building_rate: string;
      total_rate: string;
      image_url: string | null;
    }[];
  }[];
  materials: { item_name: string; net_rate: string; image_url: string | null }[];
  buildings: { building_name: string; count: string; image_url: string | null }[];
  graph_nodes: { id: string; label: string; kind: string; image_url: string | null }[];
  graph_edges: { id: string; source: string; target: string; label: string }[];
};

export type ApiErrorPayload = {
  trace_id?: string;
  error_type?: string;
  message?: string;
  stack?: string;
  detail?: string;
  context?: Record<string, unknown>;
};
