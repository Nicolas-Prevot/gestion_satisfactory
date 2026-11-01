import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ConflictModal } from "../components/ConflictModal";
import { Toast } from "../components/Toast";
import { useErrorStore } from "../features/errorStore";
import { usePlannerStore } from "../features/plannerStore";
import {
  createArea,
  createFactory,
  createLine,
  createScenario,
  deleteArea,
  deleteFactory,
  deleteLine,
  deleteScenario,
  extractApiError,
  getBalances,
  isConflictError,
  listAreas,
  listBuildings,
  listFactories,
  listItems,
  listLines,
  listRecipes,
  listScenarios,
  updateArea,
  updateFactory,
  updateLine,
} from "../lib/api";
import { resolveImageSrc } from "../lib/images";
import type { Area, ConflictResponse, Factory, Line, Recipe } from "../lib/types";
import { useScenarioWebSocket } from "../lib/ws";

type DraftLine = {
  id: number | null;
  version: number;
  name: string;
  area_id: number;
  factory_id: number | null;
  recipe_id: number;
  building_count: number;
  efficiency_multiplier: string;
};

function emptyDraft(areas: Area[], recipes: Recipe[]): DraftLine {
  return {
    id: null,
    version: 1,
    name: "",
    area_id: areas[0]?.id ?? 0,
    factory_id: null,
    recipe_id: recipes[0]?.id ?? 0,
    building_count: 1,
    efficiency_multiplier: "1.0",
  };
}

type LineFlowItem = {
  item_name: string;
  base_rate: number;
  total_rate: number;
  image_url: string | null;
};

function formatRate(value: number): string {
  if (!Number.isFinite(value)) return "0";
  const roundedInt = Math.round(value);
  if (Math.abs(value - roundedInt) <= 0.000001) {
    return String(roundedInt);
  }
  return value.toFixed(6).replace(/\.?0+$/, "");
}

function formatSummaryRate(value: string): string {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) return value;
  const roundedInt = Math.round(parsed);
  if (Math.abs(parsed - roundedInt) <= 0.000001) {
    return String(roundedInt);
  }
  return parsed.toFixed(6).replace(/\.?0+$/, "");
}

function withSign(rate: string, sign: "+" | "-"): string {
  const formatted = formatSummaryRate(rate);
  const abs = formatted.replace(/^[-+]/, "");
  return `${sign}${abs}`;
}

function computeRatePerMinute(amount: number | null, duration: number, buildingCount: number, efficiency: number): number {
  if (amount === null || duration <= 0) return 0;
  return (60 * amount * buildingCount * efficiency) / duration;
}

function lineFlowFromRecipe(
  line: Line,
  recipe: Recipe | undefined,
  itemImageByName: Map<string, string | null>,
): {
  outputs: LineFlowItem[];
  inputs: LineFlowItem[];
} {
  if (!recipe) {
    return { outputs: [], inputs: [] };
  }
  const efficiency = Number.parseFloat(line.efficiency_multiplier) || 0;

  const outputs: LineFlowItem[] = [];
  const inputs: LineFlowItem[] = [];

  for (let index = 1 as const; index <= 2; index += 1) {
    const itemName = recipe[`product_${index}`];
    const amount = recipe[`product_amount_${index}`];
    if (!itemName || amount === null) continue;
    const baseRate = computeRatePerMinute(amount, recipe.duration, 1, 1);
    const totalRate = computeRatePerMinute(amount, recipe.duration, line.building_count, efficiency);
    outputs.push({
      item_name: itemName,
      base_rate: baseRate,
      total_rate: totalRate,
      image_url: itemImageByName.get(itemName) ?? null,
    });
  }

  for (let index = 1 as const; index <= 4; index += 1) {
    const itemName = recipe[`ingredient_${index}`];
    const amount = recipe[`ingredient_amount_${index}`];
    if (!itemName || amount === null) continue;
    const baseRate = computeRatePerMinute(amount, recipe.duration, 1, 1);
    const totalRate = computeRatePerMinute(amount, recipe.duration, line.building_count, efficiency);
    inputs.push({
      item_name: itemName,
      base_rate: baseRate,
      total_rate: totalRate,
      image_url: itemImageByName.get(itemName) ?? null,
    });
  }

  return { outputs, inputs };
}

export function PlannerPage() {
  const queryClient = useQueryClient();
  const setApiError = useErrorStore((s) => s.setError);

  const scenarioId = usePlannerStore((s) => s.scenarioId);
  const areaId = usePlannerStore((s) => s.areaId);
  const factoryId = usePlannerStore((s) => s.factoryId);
  const setScenario = usePlannerStore((s) => s.setScenario);
  const setArea = usePlannerStore((s) => s.setArea);
  const setFactory = usePlannerStore((s) => s.setFactory);

  const [newScenarioName, setNewScenarioName] = useState("");
  const [newAreaName, setNewAreaName] = useState("");
  const [newFactoryName, setNewFactoryName] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [conflict, setConflict] = useState<ConflictResponse | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const scenariosQuery = useQuery({ queryKey: ["scenarios"], queryFn: () => listScenarios(false) });

  useEffect(() => {
    if (!scenarioId && scenariosQuery.data?.length) {
      setScenario(scenariosQuery.data[0].id);
    }
  }, [scenarioId, scenariosQuery.data, setScenario]);

  const areasQuery = useQuery({
    queryKey: ["areas", scenarioId],
    queryFn: () => listAreas(scenarioId as number),
    enabled: !!scenarioId,
  });

  const factoriesQuery = useQuery({
    queryKey: ["factories", scenarioId],
    queryFn: () => listFactories(scenarioId as number),
    enabled: !!scenarioId,
  });

  const scopedLinesQuery = useQuery({
    queryKey: ["lines", scenarioId, areaId, factoryId],
    queryFn: () => listLines(scenarioId as number, areaId ?? undefined, factoryId ?? undefined),
    enabled: !!scenarioId,
  });
  const treeLinesQuery = useQuery({
    queryKey: ["lines-tree", scenarioId],
    queryFn: () => listLines(scenarioId as number),
    enabled: !!scenarioId,
  });

  const recipesQuery = useQuery({ queryKey: ["recipes"], queryFn: () => listRecipes(), enabled: !!scenarioId });
  const itemsQuery = useQuery({ queryKey: ["items"], queryFn: listItems });
  const buildingsQuery = useQuery({ queryKey: ["buildings"], queryFn: listBuildings });

  const balancesQuery = useQuery({
    queryKey: ["balances", scenarioId, areaId, factoryId],
    queryFn: () => getBalances(scenarioId as number, areaId ?? undefined, factoryId ?? undefined),
    enabled: !!scenarioId,
  });

  useScenarioWebSocket(scenarioId, (event) => {
    if (event.event_type === "scenario.changed") {
      setToastMessage(`${event.entity_type} ${event.action}`);
      queryClient.invalidateQueries({ queryKey: ["areas", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["factories", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
      window.setTimeout(() => setToastMessage(null), 2200);
    }
  });

  const createScenarioMutation = useMutation({
    mutationFn: (name: string) => createScenario(name),
    onSuccess: (created) => {
      setNewScenarioName("");
      setScenario(created.id);
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const createAreaMutation = useMutation({
    mutationFn: (name: string) => createArea(scenarioId as number, { name }),
    onSuccess: () => {
      setNewAreaName("");
      queryClient.invalidateQueries({ queryKey: ["areas", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const createFactoryMutation = useMutation({
    mutationFn: (name: string) =>
      createFactory(scenarioId as number, { area_id: areaId as number, name }),
    onSuccess: () => {
      setNewFactoryName("");
      queryClient.invalidateQueries({ queryKey: ["factories", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const updateAreaMutation = useMutation({
    mutationFn: ({ targetAreaId, name }: { targetAreaId: number; name: string }) =>
      updateArea(targetAreaId, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["areas", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const updateFactoryMutation = useMutation({
    mutationFn: ({
      targetFactoryId,
      areaId: nextAreaId,
      name,
    }: {
      targetFactoryId: number;
      areaId: number;
      name: string;
    }) => updateFactory(targetFactoryId, { area_id: nextAreaId, name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["factories", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const [draft, setDraft] = useState<DraftLine | null>(null);

  useEffect(() => {
    if (!draft && areasQuery.data && recipesQuery.data) {
      const initial = emptyDraft(areasQuery.data, recipesQuery.data);
      if (initial.area_id && initial.recipe_id) {
        setDraft(initial);
      }
    }
  }, [areasQuery.data, recipesQuery.data, draft]);

  const saveLineMutation = useMutation({
    mutationFn: async (currentDraft: DraftLine) => {
      if (!currentDraft.id) {
        return createLine(scenarioId as number, {
          area_id: currentDraft.area_id,
          factory_id: currentDraft.factory_id,
          name: currentDraft.name,
          recipe_id: currentDraft.recipe_id,
          building_count: currentDraft.building_count,
          efficiency_multiplier: currentDraft.efficiency_multiplier,
        });
      }
      return updateLine(currentDraft.id, {
        version: currentDraft.version,
        area_id: currentDraft.area_id,
        factory_id: currentDraft.factory_id,
        name: currentDraft.name,
        recipe_id: currentDraft.recipe_id,
        building_count: currentDraft.building_count,
        efficiency_multiplier: currentDraft.efficiency_multiplier,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
      setDrawerOpen(false);
      if (areasQuery.data && recipesQuery.data) {
        setDraft(emptyDraft(areasQuery.data, recipesQuery.data));
      }
    },
    onError: (error) => {
      const maybeConflict = isConflictError(error);
      if (maybeConflict) {
        setConflict(maybeConflict);
        return;
      }
      setApiError(extractApiError(error));
    },
  });

  const deleteLineMutation = useMutation({
    mutationFn: ({ lineId, version }: { lineId: number; version: number }) => deleteLine(lineId, version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
    },
    onError: (error) => {
      const maybeConflict = isConflictError(error);
      if (maybeConflict) {
        setConflict(maybeConflict);
        return;
      }
      setApiError(extractApiError(error));
    },
  });

  const deleteAreaMutation = useMutation({
    mutationFn: (targetAreaId: number) => deleteArea(targetAreaId),
    onSuccess: () => {
      if (areaId) setArea(null);
      queryClient.invalidateQueries({ queryKey: ["areas", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["factories", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const deleteFactoryMutation = useMutation({
    mutationFn: (targetFactoryId: number) => deleteFactory(targetFactoryId),
    onSuccess: () => {
      if (factoryId) setFactory(null);
      queryClient.invalidateQueries({ queryKey: ["factories", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
      queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const deleteScenarioMutation = useMutation({
    mutationFn: (id: number) => deleteScenario(id),
    onSuccess: () => {
      setScenario(null);
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
      queryClient.invalidateQueries({ queryKey: ["areas"] });
      queryClient.invalidateQueries({ queryKey: ["factories"] });
      queryClient.invalidateQueries({ queryKey: ["lines"] });
      queryClient.invalidateQueries({ queryKey: ["lines-tree"] });
    },
    onError: (error) => setApiError(extractApiError(error)),
  });

  const areas = areasQuery.data ?? [];
  const factories = factoriesQuery.data ?? [];
  const lines = scopedLinesQuery.data ?? [];
  const treeLines = treeLinesQuery.data ?? [];
  const recipes = recipesQuery.data ?? [];
  const items = itemsQuery.data ?? [];
  const buildings = buildingsQuery.data ?? [];

  const recipeById = useMemo(() => new Map(recipes.map((recipe) => [recipe.id, recipe])), [recipes]);
  const itemImageByName = useMemo(
    () => new Map(items.map((item) => [item.name, resolveImageSrc(item.image_url) ?? null])),
    [items],
  );
  const buildingImageByName = useMemo(
    () => new Map(buildings.map((building) => [building.name, resolveImageSrc(building.image_url) ?? null])),
    [buildings],
  );

  const selectedScenarioName = useMemo(
    () => scenariosQuery.data?.find((scenario) => scenario.id === scenarioId)?.name ?? null,
    [scenariosQuery.data, scenarioId],
  );
  const selectedAreaName = useMemo(
    () => areas.find((area) => area.id === areaId)?.name ?? null,
    [areas, areaId],
  );
  const selectedFactoryName = useMemo(
    () => factories.find((factory) => factory.id === factoryId)?.name ?? null,
    [factories, factoryId],
  );

  const scopeTitle = factoryId
    ? `Factory: ${selectedFactoryName ?? "-"}`
    : areaId
      ? `Area: ${selectedAreaName ?? "-"}`
      : `Scenario: ${selectedScenarioName ?? "-"}`;

  const factoriesByArea = useMemo(() => {
    const map = new Map<number, Factory[]>();
    for (const factory of factories) {
      const list = map.get(factory.area_id) ?? [];
      list.push(factory);
      map.set(factory.area_id, list);
    }
    return map;
  }, [factories]);

  const treeLineNamesByFactory = useMemo(() => {
    const map = new Map<number, string[]>();
    const seenByFactory = new Map<number, Set<string>>();
    for (const line of treeLines) {
      if (line.factory_id === null) continue;
      const seen = seenByFactory.get(line.factory_id) ?? new Set<string>();
      if (seen.has(line.name)) continue;
      seen.add(line.name);
      seenByFactory.set(line.factory_id, seen);
      const list = map.get(line.factory_id) ?? [];
      list.push(line.name);
      map.set(line.factory_id, list);
    }
    return map;
  }, [treeLines]);

  const treeAreaOnlyLineNamesByArea = useMemo(() => {
    const map = new Map<number, string[]>();
    const seenByArea = new Map<number, Set<string>>();
    for (const line of treeLines) {
      if (line.factory_id !== null) continue;
      const seen = seenByArea.get(line.area_id) ?? new Set<string>();
      if (seen.has(line.name)) continue;
      seen.add(line.name);
      seenByArea.set(line.area_id, seen);
      const list = map.get(line.area_id) ?? [];
      list.push(line.name);
      map.set(line.area_id, list);
    }
    return map;
  }, [treeLines]);

  const filteredFactories = useMemo(
    () => factories.filter((factory) => factory.area_id === (draft?.area_id ?? areaId ?? -1)),
    [factories, draft?.area_id, areaId],
  );

  const groupedLines = useMemo(() => {
    const groups = new Map<string, { key: string; name: string; area_id: number; factory_id: number | null; entries: Line[] }>();
    for (const line of lines) {
      const key = `${line.name}::${line.area_id}::${line.factory_id ?? "none"}`;
      const existing = groups.get(key);
      if (existing) {
        existing.entries.push(line);
      } else {
        groups.set(key, {
          key,
          name: line.name,
          area_id: line.area_id,
          factory_id: line.factory_id,
          entries: [line],
        });
      }
    }
    return Array.from(groups.values());
  }, [lines]);

  const renameArea = (area: Area) => {
    const nextName = window.prompt("Rename area", area.name);
    if (nextName === null) return;
    const trimmed = nextName.trim();
    if (!trimmed || trimmed === area.name) return;
    updateAreaMutation.mutate({ targetAreaId: area.id, name: trimmed });
  };

  const renameFactory = (factory: Factory) => {
    const nextName = window.prompt("Rename factory", factory.name);
    if (nextName === null) return;
    const trimmed = nextName.trim();
    if (!trimmed || trimmed === factory.name) return;
    updateFactoryMutation.mutate({
      targetFactoryId: factory.id,
      areaId: factory.area_id,
      name: trimmed,
    });
  };

  return (
    <div className="planner-page">
      <Toast message={toastMessage} />
      <ConflictModal
        conflict={conflict}
        onClose={() => setConflict(null)}
        onRefresh={() => {
          setConflict(null);
          queryClient.invalidateQueries({ queryKey: ["lines", scenarioId] });
          queryClient.invalidateQueries({ queryKey: ["lines-tree", scenarioId] });
          queryClient.invalidateQueries({ queryKey: ["balances", scenarioId] });
        }}
      />

      <section className="planner-layout">
        <aside className="panel tree-panel">
          <details className="scenario-foldout" open>
            <summary>Scenario</summary>
            <div className="scenario-compact-controls">
              <select
                id="scenario-select"
                value={scenarioId ?? ""}
                onChange={(event) => setScenario(Number(event.target.value) || null)}
              >
                <option value="">Select scenario</option>
                {scenariosQuery.data?.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </option>
                ))}
              </select>

              <div className="inline-actions scenario-add-row">
                <input
                  value={newScenarioName}
                  onChange={(event) => setNewScenarioName(event.target.value)}
                  placeholder="New scenario"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (!newScenarioName.trim()) return;
                    createScenarioMutation.mutate(newScenarioName.trim());
                  }}
                >
                  Add
                </button>
              </div>

              {scenarioId ? (
                <button
                  type="button"
                  className="danger"
                  onClick={() => {
                    if (window.confirm("Delete this scenario and all linked data?")) {
                      deleteScenarioMutation.mutate(scenarioId);
                    }
                  }}
                >
                  Delete scenario
                </button>
              ) : null}
            </div>
          </details>

          <h3>Area / Factory / Lines</h3>
          <button
            type="button"
            className="secondary tree-scope-reset"
            disabled={!scenarioId || (!areaId && !factoryId)}
            onClick={() => {
              setArea(null);
              setFactory(null);
            }}
          >
            View scenario scope
          </button>

          <div className="inline-actions">
            <input
              value={newAreaName}
              onChange={(event) => setNewAreaName(event.target.value)}
              placeholder="Add area"
              disabled={!scenarioId}
            />
            <button
              type="button"
              disabled={!scenarioId}
              onClick={() => {
                if (!newAreaName.trim()) return;
                createAreaMutation.mutate(newAreaName.trim());
              }}
            >
              +
            </button>
          </div>

          <div className="inline-actions">
            <input
              value={newFactoryName}
              onChange={(event) => setNewFactoryName(event.target.value)}
              placeholder="Add factory"
              disabled={!scenarioId || !areaId}
            />
            <button
              type="button"
              disabled={!scenarioId || !areaId}
              onClick={() => {
                if (!newFactoryName.trim()) return;
                createFactoryMutation.mutate(newFactoryName.trim());
              }}
            >
              +
            </button>
          </div>

          <button
            type="button"
            className="add-line-trigger"
            disabled={!scenarioId || !areas.length || !recipes.length}
            onClick={() => {
              const base = emptyDraft(areas, recipes);
              setDraft({ ...base, area_id: areaId ?? base.area_id, factory_id: factoryId ?? null });
              setDrawerOpen(true);
            }}
          >
            Add line
          </button>

          <div className="tree-scroll">
            {areas.map((area) => {
              const areaFactories = factoriesByArea.get(area.id) ?? [];
              const areaOnlyLineNames = treeAreaOnlyLineNamesByArea.get(area.id) ?? [];
              return (
                <div
                  key={area.id}
                  className={area.id === areaId ? "tree-node area-node active" : "tree-node area-node"}
                >
                  <div className="tree-node-row">
                    <button
                      type="button"
                      onClick={() => {
                        if (areaId === area.id && !factoryId) {
                          setArea(null);
                          return;
                        }
                        setArea(area.id);
                      }}
                    >
                      {area.name}
                    </button>
                    <button
                      type="button"
                      className="secondary tree-node-edit"
                      title="Rename area"
                      disabled={updateAreaMutation.isPending}
                      onClick={() => renameArea(area)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="danger"
                      title="Delete area"
                      onClick={() => {
                        if (window.confirm(`Delete area '${area.name}'?`)) {
                          deleteAreaMutation.mutate(area.id);
                        }
                      }}
                    >
                      x
                    </button>
                  </div>

                  {areaFactories.map((factory) => {
                    const factoryLineNames = treeLineNamesByFactory.get(factory.id) ?? [];
                    return (
                      <div
                        key={factory.id}
                        className={factory.id === factoryId ? "tree-subnode factory-node active" : "tree-subnode factory-node"}
                      >
                        <div className="tree-node-row">
                          <button
                            type="button"
                            onClick={() => {
                              if (factoryId === factory.id) {
                                setFactory(null);
                                return;
                              }
                              setArea(area.id);
                              setFactory(factory.id);
                            }}
                          >
                            {factory.name}
                          </button>
                          <button
                            type="button"
                            className="secondary tree-node-edit"
                            title="Rename factory"
                            disabled={updateFactoryMutation.isPending}
                            onClick={() => renameFactory(factory)}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="danger"
                            title="Delete factory"
                            onClick={() => {
                              if (window.confirm(`Delete factory '${factory.name}'?`)) {
                                deleteFactoryMutation.mutate(factory.id);
                              }
                            }}
                          >
                            x
                          </button>
                        </div>
                        {factoryLineNames.length ? (
                          <ul className="tree-line-list">
                            {factoryLineNames.map((lineName) => (
                              <li key={`${factory.id}-${lineName}`}>{lineName}</li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    );
                  })}

                  {areaOnlyLineNames.length ? (
                    <div className="tree-area-lines">
                      <ul className="tree-line-list area-line-list">
                        {areaOnlyLineNames.map((lineName) => (
                          <li key={`${area.id}-${lineName}`}>{lineName}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </aside>

        <main className="planner-main">
          <section className="panel workspace-summary">
            <header className="workspace-summary-head">
              <h2>{scopeTitle}</h2>
              <strong className="workspace-summary-power">Power: {formatSummaryRate(balancesQuery.data?.power_mw ?? "0")} MW</strong>
            </header>

            <div className="balance-grid">
              <article>
                <h4>Outputs</h4>
                <ul>
                  {balancesQuery.data?.outputs.slice(0, 12).map((entry) => (
                    <li key={`out-${entry.item_name}`}>
                      {entry.image_url ? <img src={resolveImageSrc(entry.image_url)} alt={entry.item_name} loading="lazy" /> : null}
                      <span>{entry.item_name}</span>
                      <strong className="summary-total">{formatSummaryRate(entry.net_rate)}/min</strong>
                    </li>
                  ))}
                </ul>
              </article>

              <article>
                <h4>Intermediates</h4>
                <ul>
                  {balancesQuery.data?.intermediates.slice(0, 12).map((entry) => (
                    <li key={`mid-${entry.item_name}`}>
                      {entry.image_url ? <img src={resolveImageSrc(entry.image_url)} alt={entry.item_name} loading="lazy" /> : null}
                      <span>{entry.item_name}</span>
                      <div className="intermediate-rate-block">
                        <strong className="summary-total">{formatSummaryRate(entry.net_rate)}/min</strong>
                        <small>
                          (<span className="intermediate-produced">{withSign(entry.produced_rate, "+")}</span>
                          <span className="intermediate-divider"> | </span>
                          <span className="intermediate-consumed">{withSign(entry.consumed_rate, "-")}</span>)
                        </small>
                      </div>
                    </li>
                  ))}
                </ul>
              </article>

              <article>
                <h4>Inputs</h4>
                <ul>
                  {balancesQuery.data?.inputs.slice(0, 12).map((entry) => (
                    <li key={`in-${entry.item_name}`}>
                      {entry.image_url ? <img src={resolveImageSrc(entry.image_url)} alt={entry.item_name} loading="lazy" /> : null}
                      <span>{entry.item_name}</span>
                      <strong className="summary-total">{formatSummaryRate(entry.net_rate)}/min</strong>
                    </li>
                  ))}
                </ul>
              </article>
            </div>
          </section>

          <section className="line-card-grid">
            {groupedLines.map((group) => (
              <article key={group.key} className="line-card line-card-expanded">
                <header className="line-card-head line-card-group-head">
                  <h4>{group.name}</h4>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      const base = emptyDraft(areas, recipes);
                      const first = group.entries[0];
                      setDraft({
                        ...base,
                        name: group.name,
                        area_id: first?.area_id ?? base.area_id,
                        factory_id: first?.factory_id ?? null,
                        recipe_id: first?.recipe_id ?? base.recipe_id,
                      });
                      setDrawerOpen(true);
                    }}
                  >
                    Add recipe
                  </button>
                </header>

                <div className="line-recipe-stack">
                  {group.entries.map((line) => (
                    <section key={line.id} className="line-recipe-row">
                      {(() => {
                        const recipe = recipeById.get(line.recipe_id);
                        const flow = lineFlowFromRecipe(line, recipe, itemImageByName);
                        return (
                          <div className="line-flow-row">
                            <div className="line-flow-column outputs">
                              <div className="line-flow-items">
                                {flow.outputs.map((output) => (
                                  <article key={`${line.id}-out-${output.item_name}`} className="line-flow-item">
                                    {output.image_url ? (
                                      <img src={resolveImageSrc(output.image_url)} alt={output.item_name} loading="lazy" />
                                    ) : null}
                                    <span className="line-flow-item-name">{output.item_name}</span>
                                    <span className="line-flow-item-rate">Base: {formatRate(output.base_rate)}/min</span>
                                    <span className="line-flow-item-rate total">Total: {formatRate(output.total_rate)}/min</span>
                                  </article>
                                ))}
                                {!flow.outputs.length ? <p className="empty">No outputs</p> : null}
                              </div>
                            </div>

                            <div className="line-building-column">
                              <div className="line-building-chip">
                                <span className="line-building-recipe">{line.recipe_name}</span>
                                {buildingImageByName.get(line.building_name) ? (
                                  <img
                                    src={buildingImageByName.get(line.building_name) ?? undefined}
                                    alt={line.building_name}
                                    loading="lazy"
                                  />
                                ) : null}
                                <strong>{line.building_name}</strong>
                                <div className="line-building-meta">
                                  <span>Buildings: {line.building_count}</span>
                                  <span>Efficiency: {line.efficiency_multiplier}x</span>
                                </div>
                              </div>
                            </div>

                            <div className="line-flow-column inputs">
                              <div className="line-flow-items">
                                {flow.inputs.map((input) => (
                                  <article key={`${line.id}-in-${input.item_name}`} className="line-flow-item">
                                    {input.image_url ? (
                                      <img src={resolveImageSrc(input.image_url)} alt={input.item_name} loading="lazy" />
                                    ) : null}
                                    <span className="line-flow-item-name">{input.item_name}</span>
                                    <span className="line-flow-item-rate">Base: {formatRate(input.base_rate)}/min</span>
                                    <span className="line-flow-item-rate total">Total: {formatRate(input.total_rate)}/min</span>
                                  </article>
                                ))}
                                {!flow.inputs.length ? <p className="empty">No inputs</p> : null}
                              </div>
                            </div>

                            <div className="line-recipe-actions">
                              <button
                                type="button"
                                onClick={() => {
                                  setDraft({
                                    id: line.id,
                                    version: line.version,
                                    name: line.name,
                                    area_id: line.area_id,
                                    factory_id: line.factory_id,
                                    recipe_id: line.recipe_id,
                                    building_count: line.building_count,
                                    efficiency_multiplier: line.efficiency_multiplier,
                                  });
                                  setDrawerOpen(true);
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="danger line-delete-icon"
                                title={`Delete line '${line.name}'`}
                                onClick={() => {
                                  if (!window.confirm(`Delete line '${line.name}'?`)) return;
                                  deleteLineMutation.mutate({ lineId: line.id, version: line.version });
                                }}
                              >
                                x
                              </button>
                            </div>
                          </div>
                        );
                      })()}
                    </section>
                  ))}
                </div>
              </article>
            ))}
            {!groupedLines.length ? <p className="empty">No lines in current scope.</p> : null}
          </section>
        </main>
      </section>

      <section className={drawerOpen ? "drawer open" : "drawer"}>
        <header>
          <h3>{draft?.id ? "Edit line" : "Create line"}</h3>
          <button type="button" onClick={() => setDrawerOpen(false)}>
            Close
          </button>
        </header>

        {draft ? (
          <form
            className="drawer-form"
            onSubmit={(event) => {
              event.preventDefault();
              if (!draft.name.trim()) return;
              saveLineMutation.mutate(draft);
            }}
          >
            <label>
              Name
              <input
                value={draft.name}
                onChange={(event) => setDraft({ ...draft, name: event.target.value })}
                placeholder="Line name"
                required
              />
            </label>

            <label>
              Area
              <select
                value={draft.area_id}
                onChange={(event) =>
                  setDraft({ ...draft, area_id: Number(event.target.value), factory_id: null })
                }
                required
              >
                {areas.map((area) => (
                  <option key={area.id} value={area.id}>
                    {area.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Factory (optional)
              <select
                value={draft.factory_id ?? ""}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    factory_id: event.target.value ? Number(event.target.value) : null,
                  })
                }
              >
                <option value="">No factory</option>
                {filteredFactories.map((factory) => (
                  <option key={factory.id} value={factory.id}>
                    {factory.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Recipe
              <select
                value={draft.recipe_id}
                onChange={(event) => setDraft({ ...draft, recipe_id: Number(event.target.value) })}
                required
              >
                {recipes.map((recipe) => (
                  <option key={recipe.id} value={recipe.id}>
                    {recipe.recipe_name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Number of buildings
              <input
                type="number"
                min={1}
                step={1}
                value={draft.building_count}
                onChange={(event) => setDraft({ ...draft, building_count: Number(event.target.value) || 1 })}
                required
              />
            </label>

            <label>
              Efficiency multiplier
              <input
                value={draft.efficiency_multiplier}
                onChange={(event) => setDraft({ ...draft, efficiency_multiplier: event.target.value })}
                placeholder="1.0"
                required
              />
            </label>

            <button type="submit" disabled={saveLineMutation.isPending}>
              {saveLineMutation.isPending ? "Saving..." : "Save line"}
            </button>
          </form>
        ) : (
          <p>No editable line selected.</p>
        )}
      </section>
    </div>
  );
}
