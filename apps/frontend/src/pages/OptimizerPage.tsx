import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import ReactFlow, {
  Background,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  MarkerType,
  MiniMap,
  Position,
  getBezierPath,
  type Edge,
  type EdgeProps,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

import { useErrorStore } from "../features/errorStore";
import { extractApiError, listBuildings, listItems, listRecipes, solveOptimizer } from "../lib/api";
import { resolveImageSrc } from "../lib/images";
import type { OptimizerRequest, OptimizerResult } from "../lib/types";

const DEFAULT_WEIGHTS: Record<string, string> = {
  Limestone: "1.33",
  "Iron Ore": "1",
  "Copper Ore": "2.5",
  Coal: "2.18",
  Sulfur: "8.53",
  "Raw Quartz": "6.82",
  Bauxite: "7.49",
  "Caterium Ore": "6.14",
  Water: "0",
  "Crude Oil": "7.31",
  "Nitrogen Gas": "7.68",
  Uranium: "43.86",
  SAM: "9.04",
  Mycelia: "1",
  Leaves: "1",
  Wood: "1",
  "Blue Power Slug": "1",
  "Purple Power Slug": "1",
  "Yellow Power Slug": "1",
  "Stinger Remains": "1",
  "Hog Remains": "1",
  "Hatcher Remains": "1",
  "Spitter Remains": "1",
  "FICSMAS Tree Branch": "1",
  "FICSMAS Bow": "1",
  "Actual Snow": "1",
  "Candy Cane": "1",
};

const DEFAULT_LIMITS: Record<string, string> = {
  Limestone: "69300",
  "Iron Ore": "92100",
  "Copper Ore": "36900",
  Coal: "42300",
  Sulfur: "10800",
  "Raw Quartz": "13500",
  Bauxite: "12300",
  "Caterium Ore": "15000",
  Water: "53125",
  "Crude Oil": "12600",
  "Nitrogen Gas": "12000",
  Uranium: "2100",
  SAM: "10200",
  Mycelia: "200",
  Leaves: "200",
  Wood: "200",
  "Blue Power Slug": "200",
  "Purple Power Slug": "200",
  "Yellow Power Slug": "200",
  "Stinger Remains": "200",
  "Hog Remains": "200",
  "Hatcher Remains": "200",
  "Spitter Remains": "200",
  "FICSMAS Tree Branch": "200",
  "FICSMAS Bow": "200",
  "Actual Snow": "200",
  "Candy Cane": "200",
};
const RAW_ITEM_NAMES = new Set([...Object.keys(DEFAULT_WEIGHTS), ...Object.keys(DEFAULT_LIMITS)]);
const EDGE_LANE_SPACING = 12;

type LaneEdgeData = {
  lane_offset: number;
  is_feedback: boolean;
};

function LaneBezierEdge(props: EdgeProps<LaneEdgeData>) {
  const laneOffset = props.data?.lane_offset ?? 0;
  const isFeedback = props.data?.is_feedback ?? false;
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY + laneOffset,
    targetX: props.targetX,
    targetY: props.targetY + laneOffset,
    sourcePosition: props.sourcePosition,
    targetPosition: props.targetPosition,
    curvature: isFeedback ? 0.42 : 0.28 + Math.min(Math.abs(laneOffset) / 120, 0.16),
  });
  return (
    <>
      <BaseEdge id={props.id} path={edgePath} markerEnd={props.markerEnd} style={props.style} />
      {props.label ? (
        <EdgeLabelRenderer>
          <div
            className="graph-edge-label nodrag nopan"
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
          >
            {props.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}

const EDGE_TYPES = { laneBezier: LaneBezierEdge };

function upsertEntry(entries: { item_name: string; quantity: string }[], itemName: string) {
  if (entries.find((entry) => entry.item_name === itemName)) {
    return entries;
  }
  return [...entries, { item_name: itemName, quantity: "0" }];
}

function parseEdgeRate(label: string): number {
  const parsed = Number(label.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatBuildingCount(value: string): string {
  const normalized = value.replace(",", ".");
  const parsed = Number.parseFloat(normalized);
  if (!Number.isFinite(parsed)) return value;
  const trimmed = parsed.toFixed(6).replace(/\.?0+$/, "");
  return trimmed.includes(".") ? trimmed : `${trimmed}.0`;
}

function graphNodeWidth(label: string, kind: string): number {
  const length = label.length;
  if (kind === "recipe") {
    if (length <= 14) return 172;
    if (length <= 24) return 186;
    if (length <= 34) return 200;
    return 214;
  }
  if (length <= 12) return 164;
  if (length <= 22) return 178;
  if (length <= 30) return 192;
  return 206;
}

function toGraph(result: OptimizerResult, selectedTargetItems: string[]): { nodes: Node[]; edges: Edge[] } {
  if (!result.graph_nodes.length) {
    return { nodes: [], edges: [] };
  }

  const nodeMap = new Map(result.graph_nodes.map((node) => [node.id, node]));
  const outgoing = new Map<string, string[]>();
  const incoming = new Map<string, string[]>();
  for (const node of result.graph_nodes) {
    outgoing.set(node.id, []);
    incoming.set(node.id, []);
  }
  for (const edge of result.graph_edges) {
    if (!nodeMap.has(edge.source) || !nodeMap.has(edge.target)) continue;
    outgoing.get(edge.source)?.push(edge.target);
    incoming.get(edge.target)?.push(edge.source);
  }

  const selectedTargetIds = selectedTargetItems
    .map((itemName) => `item::${itemName}`)
    .filter((id) => nodeMap.has(id));
  const itemNodeIds = result.graph_nodes.filter((node) => node.kind === "item").map((node) => node.id);

  let anchors = selectedTargetIds;
  if (!anchors.length) {
    anchors = itemNodeIds.filter((id) => (outgoing.get(id)?.length ?? 0) === 0);
  }
  if (!anchors.length) {
    anchors = result.materials
      .map((material) => ({
        id: `item::${material.item_name}`,
        rate: Number(material.net_rate.replace(",", ".")),
      }))
      .filter((entry) => nodeMap.has(entry.id) && Number.isFinite(entry.rate) && entry.rate > 0)
      .sort((a, b) => b.rate - a.rate)
      .slice(0, 3)
      .map((entry) => entry.id);
  }
  if (!anchors.length) {
    anchors = [result.graph_nodes[0].id];
  }

  const layerByNode = new Map<string, number>();
  const queue: string[] = [];
  for (const anchorId of anchors) {
    if (!layerByNode.has(anchorId)) {
      layerByNode.set(anchorId, 0);
      queue.push(anchorId);
    }
  }

  while (queue.length) {
    const current = queue.shift();
    if (!current) continue;
    const currentLayer = layerByNode.get(current) ?? 0;
    for (const previousNode of incoming.get(current) ?? []) {
      const nextLayer = currentLayer + 1;
      const knownLayer = layerByNode.get(previousNode);
      if (knownLayer === undefined || nextLayer < knownLayer) {
        layerByNode.set(previousNode, nextLayer);
        queue.push(previousNode);
      }
    }
  }

  let maxLayer = Math.max(...Array.from(layerByNode.values()), 0);
  for (const node of result.graph_nodes) {
    if (layerByNode.has(node.id)) continue;
    const isRawItem = node.kind === "item" && RAW_ITEM_NAMES.has(node.label);
    const hasProducer = (incoming.get(node.id)?.length ?? 0) > 0;
    layerByNode.set(node.id, isRawItem || !hasProducer ? maxLayer + 2 : maxLayer + 1);
  }
  maxLayer = Math.max(...Array.from(layerByNode.values()), 0);

  const layers = new Map<number, string[]>();
  for (const node of result.graph_nodes) {
    const layer = layerByNode.get(node.id) ?? 0;
    const bucket = layers.get(layer);
    if (bucket) {
      bucket.push(node.id);
    } else {
      layers.set(layer, [node.id]);
    }
  }

  const selectedTargetSet = new Set(selectedTargetItems);
  const materialRateMap = new Map(result.materials.map((material) => [material.item_name, material.net_rate]));
  const orderedLayers = Array.from(layers.keys()).sort((a, b) => a - b);

  for (const layer of orderedLayers) {
    const nodesInLayer = layers.get(layer) ?? [];
    nodesInLayer.sort((a, b) => {
      const nodeA = nodeMap.get(a);
      const nodeB = nodeMap.get(b);
      if (!nodeA || !nodeB) return 0;
      const aIsTarget = nodeA.kind === "item" && selectedTargetSet.has(nodeA.label) ? 0 : 1;
      const bIsTarget = nodeB.kind === "item" && selectedTargetSet.has(nodeB.label) ? 0 : 1;
      if (aIsTarget !== bIsTarget) return aIsTarget - bIsTarget;
      const aKindOrder = nodeA.kind === "item" ? 0 : 1;
      const bKindOrder = nodeB.kind === "item" ? 0 : 1;
      if (aKindOrder !== bKindOrder) return aKindOrder - bKindOrder;
      return nodeA.label.localeCompare(nodeB.label);
    });
  }

  const layerOrderIndex = (): Map<number, Map<string, number>> => {
    const indexMap = new Map<number, Map<string, number>>();
    for (const layer of orderedLayers) {
      const ids = layers.get(layer) ?? [];
      const indices = new Map<string, number>();
      ids.forEach((id, index) => indices.set(id, index));
      indexMap.set(layer, indices);
    }
    return indexMap;
  };

  const averageNeighborIndex = (
    nodeId: string,
    targetLayer: number,
    indexMap: Map<number, Map<string, number>>,
  ): number | null => {
    const neighbors = [...(incoming.get(nodeId) ?? []), ...(outgoing.get(nodeId) ?? [])].filter(
      (neighbor) => (layerByNode.get(neighbor) ?? -1) === targetLayer,
    );
    if (!neighbors.length) return null;
    const indexes = neighbors
      .map((neighbor) => indexMap.get(targetLayer)?.get(neighbor))
      .filter((value): value is number => value !== undefined);
    if (!indexes.length) return null;
    return indexes.reduce((sum, value) => sum + value, 0) / indexes.length;
  };

  for (let i = 1; i < orderedLayers.length; i += 1) {
    const currentLayer = orderedLayers[i];
    const previousLayer = orderedLayers[i - 1];
    const currentNodes = layers.get(currentLayer) ?? [];
    const indexMap = layerOrderIndex();
    currentNodes.sort((a, b) => {
      const scoreA = averageNeighborIndex(a, previousLayer, indexMap);
      const scoreB = averageNeighborIndex(b, previousLayer, indexMap);
      if (scoreA === null && scoreB === null) return 0;
      if (scoreA === null) return 1;
      if (scoreB === null) return -1;
      return scoreA - scoreB;
    });
  }

  for (let i = orderedLayers.length - 2; i >= 0; i -= 1) {
    const currentLayer = orderedLayers[i];
    const nextLayer = orderedLayers[i + 1];
    const currentNodes = layers.get(currentLayer) ?? [];
    const indexMap = layerOrderIndex();
    currentNodes.sort((a, b) => {
      const scoreA = averageNeighborIndex(a, nextLayer, indexMap);
      const scoreB = averageNeighborIndex(b, nextLayer, indexMap);
      if (scoreA === null && scoreB === null) return 0;
      if (scoreA === null) return 1;
      if (scoreB === null) return -1;
      return scoreA - scoreB;
    });
  }

  const xGap = 252;
  const yGap = 124;
  const nodes: Node[] = [];
  for (const layer of orderedLayers) {
    const nodesInLayer = layers.get(layer) ?? [];
    const totalHeight = (nodesInLayer.length - 1) * yGap;
    nodesInLayer.forEach((nodeId, index) => {
      const node = nodeMap.get(nodeId);
      if (!node) return;
      const isTarget = node.kind === "item" && selectedTargetSet.has(node.label);
      const isRaw = node.kind === "item" && RAW_ITEM_NAMES.has(node.label);
      nodes.push({
        id: node.id,
        position: {
          x: layer * xGap,
          y: index * yGap - totalHeight / 2,
        },
        data: {
          label: (
            <div className="graph-node">
              <div className="graph-node-icon">
                {node.image_url ? (
                  <img src={resolveImageSrc(node.image_url)} alt={node.label} loading="lazy" />
                ) : (
                  <span className="graph-node-fallback">{node.label.slice(0, 2).toUpperCase()}</span>
                )}
              </div>
              <div className="graph-node-text">
                <span className="graph-node-title">{node.label}</span>
                <div className="graph-node-meta">
                  {isTarget ? <small className="graph-badge target">Target</small> : null}
                  {!isTarget && isRaw ? <small className="graph-badge raw">Raw</small> : null}
                  {node.kind === "item" && materialRateMap.has(node.label) ? (
                    <small className="graph-rate">{materialRateMap.get(node.label)}/min</small>
                  ) : null}
                </div>
              </div>
            </div>
          ),
        },
        sourcePosition: Position.Left,
        targetPosition: Position.Right,
        type: "default",
        draggable: false,
        selectable: true,
        style: {
          background:
            node.kind === "recipe"
              ? "linear-gradient(150deg, #133846, #122f3f)"
              : isRaw
                ? "linear-gradient(150deg, #3a2733, #30202c)"
                : "linear-gradient(150deg, #1f2f42, #1a2837)",
          border: isTarget
            ? "1px solid rgba(255, 177, 0, 0.8)"
            : isRaw
              ? "1px solid rgba(239,106,103,0.55)"
              : "1px solid rgba(255,255,255,0.18)",
          borderRadius: "24px",
          color: "#f6f7f8",
          padding: "7px 9px",
          width: graphNodeWidth(node.label, node.kind),
          minHeight: 86,
          boxShadow: "0 10px 18px rgba(6, 12, 20, 0.32)",
        },
      });
    });
  }

  const layerIndexByNode = new Map<string, number>();
  for (const layer of orderedLayers) {
    const nodesInLayer = layers.get(layer) ?? [];
    nodesInLayer.forEach((nodeId, index) => layerIndexByNode.set(nodeId, index));
  }

  const pushEdgeGroup = (map: Map<string, typeof result.graph_edges>, key: string, edge: (typeof result.graph_edges)[number]) => {
    const current = map.get(key);
    if (current) {
      current.push(edge);
    } else {
      map.set(key, [edge]);
    }
  };

  const edgesBySource = new Map<string, typeof result.graph_edges>();
  const edgesByTarget = new Map<string, typeof result.graph_edges>();
  const edgesByPair = new Map<string, typeof result.graph_edges>();
  for (const edge of result.graph_edges) {
    pushEdgeGroup(edgesBySource, edge.source, edge);
    pushEdgeGroup(edgesByTarget, edge.target, edge);
    pushEdgeGroup(edgesByPair, `${edge.source}->${edge.target}`, edge);
  }

  const assignLaneOffsets = (
    groups: Map<string, typeof result.graph_edges>,
    comparator: (a: (typeof result.graph_edges)[number], b: (typeof result.graph_edges)[number]) => number,
  ): Map<string, number> => {
    const laneMap = new Map<string, number>();
    for (const groupEdges of groups.values()) {
      const ordered = [...groupEdges].sort(comparator);
      const center = (ordered.length - 1) / 2;
      ordered.forEach((edge, index) => laneMap.set(edge.id, (index - center) * EDGE_LANE_SPACING));
    }
    return laneMap;
  };

  const sourceLaneOffsets = assignLaneOffsets(edgesBySource, (a, b) => {
    const aLayer = layerByNode.get(a.target) ?? 0;
    const bLayer = layerByNode.get(b.target) ?? 0;
    if (aLayer !== bLayer) return aLayer - bLayer;
    const aIndex = layerIndexByNode.get(a.target) ?? 0;
    const bIndex = layerIndexByNode.get(b.target) ?? 0;
    if (aIndex !== bIndex) return aIndex - bIndex;
    return parseEdgeRate(b.label) - parseEdgeRate(a.label);
  });

  const targetLaneOffsets = assignLaneOffsets(edgesByTarget, (a, b) => {
    const aLayer = layerByNode.get(a.source) ?? 0;
    const bLayer = layerByNode.get(b.source) ?? 0;
    if (aLayer !== bLayer) return bLayer - aLayer;
    const aIndex = layerIndexByNode.get(a.source) ?? 0;
    const bIndex = layerIndexByNode.get(b.source) ?? 0;
    if (aIndex !== bIndex) return aIndex - bIndex;
    return parseEdgeRate(b.label) - parseEdgeRate(a.label);
  });

  const pairLaneOffsets = assignLaneOffsets(edgesByPair, (a, b) => parseEdgeRate(b.label) - parseEdgeRate(a.label));

  const edges: Edge[] = result.graph_edges.map((edge) => {
    const sourceLayer = layerByNode.get(edge.source) ?? 0;
    const targetLayer = layerByNode.get(edge.target) ?? 0;
    const isFeedback = sourceLayer <= targetLayer;
    const magnitude = Math.abs(parseEdgeRate(edge.label));
    const width = magnitude >= 100 ? 2.8 : magnitude >= 10 ? 2.2 : 1.6;
    let laneOffset =
      (sourceLaneOffsets.get(edge.id) ?? 0) - (targetLaneOffsets.get(edge.id) ?? 0) * 0.55 + (pairLaneOffsets.get(edge.id) ?? 0);
    if (isFeedback) {
      laneOffset += laneOffset >= 0 ? 18 : -18;
    }
    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: "laneBezier",
      data: {
        lane_offset: laneOffset,
        is_feedback: isFeedback,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isFeedback ? "#ef6a67" : "#8dd7c3",
      },
      style: {
        stroke: isFeedback ? "#d97472" : "#7da6b3",
        strokeWidth: width,
        strokeDasharray: isFeedback ? "6 4" : undefined,
        opacity: isFeedback ? 0.76 : 0.95,
      },
    };
  });

  return { nodes, edges };
}

export function OptimizerPage() {
  const setApiError = useErrorStore((state) => state.setError);
  const [search, setSearch] = useState("");
  const [maxTier, setMaxTier] = useState(9);
  const [selectedProducts, setSelectedProducts] = useState<{ item_name: string; quantity: string }[]>([]);
  const [availableItems, setAvailableItems] = useState<{ item_name: string; quantity: string }[]>([]);
  const [rawWeights, setRawWeights] = useState<Record<string, string>>(DEFAULT_WEIGHTS);
  const [rawLimits, setRawLimits] = useState<Record<string, string>>(DEFAULT_LIMITS);
  const [result, setResult] = useState<OptimizerResult | null>(null);

  const itemsQuery = useQuery({ queryKey: ["items"], queryFn: listItems });
  const buildingsQuery = useQuery({
    queryKey: ["buildings", "optimizer-selector"],
    queryFn: listBuildings,
  });
  const recipesByTierQuery = useQuery({
    queryKey: ["recipes", "optimizer-selector", maxTier],
    queryFn: () => listRecipes(maxTier),
  });
  const itemImageMap = useMemo(
    () => new Map((itemsQuery.data ?? []).map((item) => [item.name, resolveImageSrc(item.image_url) ?? null])),
    [itemsQuery.data],
  );

  const buildingTierByName = useMemo(
    () => new Map((buildingsQuery.data ?? []).map((building) => [building.name, building.tier])),
    [buildingsQuery.data],
  );

  const tierReachableRecipes = useMemo(
    () =>
      (recipesByTierQuery.data ?? []).filter((recipe) => {
        const buildingTier = buildingTierByName.get(recipe.building_name);
        if (typeof buildingTier === "number" && buildingTier > maxTier) {
          return false;
        }
        if (
          recipe.building_name === "Packager" &&
          (recipe.product_1 === "Empty Canister" || recipe.product_2 === "Empty Canister")
        ) {
          return false;
        }
        return !!recipe.product_1 || !!recipe.product_2;
      }),
    [recipesByTierQuery.data, buildingTierByName, maxTier],
  );

  const producibleItemNames = useMemo(() => {
    const reachable = new Set<string>(RAW_ITEM_NAMES);
    let changed = true;
    while (changed) {
      changed = false;
      for (const recipe of tierReachableRecipes) {
        const ingredients = [recipe.ingredient_1, recipe.ingredient_2, recipe.ingredient_3, recipe.ingredient_4].filter(
          (item): item is string => !!item,
        );
        if (!ingredients.every((ingredient) => reachable.has(ingredient))) {
          continue;
        }
        for (const product of [recipe.product_1, recipe.product_2]) {
          if (!product || reachable.has(product)) {
            continue;
          }
          reachable.add(product);
          changed = true;
        }
      }
    }

    const names = new Set<string>();
    for (const recipe of tierReachableRecipes) {
      for (const product of [recipe.product_1, recipe.product_2]) {
        if (product && reachable.has(product) && !RAW_ITEM_NAMES.has(product)) {
          names.add(product);
        }
      }
    }
    return names;
  }, [tierReachableRecipes]);

  const filteredItems = useMemo(() => {
    const items = (itemsQuery.data ?? []).filter(
      (item) => producibleItemNames.has(item.name) && !RAW_ITEM_NAMES.has(item.name),
    );
    if (!search.trim()) return items;
    return items.filter((item) => item.name.toLowerCase().includes(search.trim().toLowerCase()));
  }, [itemsQuery.data, producibleItemNames, search]);
  const sortedFilteredItems = useMemo(
    () => [...filteredItems].sort((a, b) => a.name.localeCompare(b.name)),
    [filteredItems],
  );
  const sortedSelectedProducts = useMemo(
    () => [...selectedProducts].sort((a, b) => a.item_name.localeCompare(b.item_name)),
    [selectedProducts],
  );
  const sortedAvailableItems = useMemo(
    () => [...availableItems].sort((a, b) => a.item_name.localeCompare(b.item_name)),
    [availableItems],
  );

  useEffect(() => {
    if (recipesByTierQuery.isLoading || buildingsQuery.isLoading) return;

    setSelectedProducts((state) => {
      const filtered = state.filter((entry) => producibleItemNames.has(entry.item_name));
      return filtered.length === state.length ? state : filtered;
    });
    setAvailableItems((state) => {
      const filtered = state.filter((entry) => producibleItemNames.has(entry.item_name));
      return filtered.length === state.length ? state : filtered;
    });
  }, [producibleItemNames, recipesByTierQuery.isLoading, buildingsQuery.isLoading]);

  const optimizeMutation = useMutation({
    mutationFn: (payload: OptimizerRequest) => solveOptimizer(payload),
    onSuccess: (payload) => setResult(payload),
    onError: (error) => setApiError(extractApiError(error)),
  });

  const graph = useMemo(() => {
    if (!result || !result.graph_nodes.length) {
      return { nodes: [], edges: [] };
    }
    return toGraph(result, selectedProducts.map((entry) => entry.item_name));
  }, [result, selectedProducts]);

  return (
    <div className="optimizer-page">
      <section className="panel optimizer-controls">
        <div className="control-row">
          <label htmlFor="tier">Max Tier</label>
          <input
            id="tier"
            type="number"
            min={0}
            max={9}
            value={maxTier}
            onChange={(event) => setMaxTier(Number(event.target.value) || 0)}
          />
        </div>

        <div className="control-row">
          <input
            placeholder="Search item"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <button
            type="button"
            onClick={() => {
              const payload: OptimizerRequest = {
                max_tier: maxTier,
                selected_products: selectedProducts,
                available_items: Object.fromEntries(availableItems.map((entry) => [entry.item_name, entry.quantity])),
                raw_weights: rawWeights,
                raw_limits: rawLimits,
              };
              optimizeMutation.mutate(payload);
            }}
          >
            Solve
          </button>
        </div>

        <div className="item-gallery">
          {itemsQuery.isLoading || buildingsQuery.isLoading || recipesByTierQuery.isLoading ? (
            <p className="empty">Loading craftable items...</p>
          ) : sortedFilteredItems.length ? (
            sortedFilteredItems.map((item) => (
              <article key={item.id}>
                {item.image_url ? <img src={resolveImageSrc(item.image_url)} alt={item.name} loading="lazy" /> : null}
                <h5>{item.name}</h5>
                <div className="inline-actions">
                  <button
                    type="button"
                    onClick={() => setSelectedProducts((state) => upsertEntry(state, item.name))}
                  >
                    Target
                  </button>
                  <button
                    type="button"
                    onClick={() => setAvailableItems((state) => upsertEntry(state, item.name))}
                  >
                    Available
                  </button>
                </div>
              </article>
            ))
          ) : (
            <p className="empty">No craftable items for this tier/search.</p>
          )}
        </div>

        <details open>
          <summary>Target quantities</summary>
          {sortedSelectedProducts.length ? (
            sortedSelectedProducts.map((entry) => (
              <div key={entry.item_name} className="entry-row">
                <div className="entry-item">
                  {itemImageMap.get(entry.item_name) ? (
                    <img src={itemImageMap.get(entry.item_name) ?? undefined} alt={entry.item_name} loading="lazy" />
                  ) : null}
                  <span>{entry.item_name}</span>
                </div>
                <input
                  value={entry.quantity}
                  onChange={(event) =>
                    setSelectedProducts((state) =>
                      state.map((current) =>
                        current.item_name === entry.item_name ? { ...current, quantity: event.target.value } : current,
                      ),
                    )
                  }
                  placeholder="0.0"
                />
                <button
                  type="button"
                  className="danger"
                  onClick={() =>
                    setSelectedProducts((state) => state.filter((current) => current.item_name !== entry.item_name))
                  }
                >
                  x
                </button>
              </div>
            ))
          ) : (
            <p>No targets selected.</p>
          )}
        </details>

        <details open>
          <summary>Already available items</summary>
          {sortedAvailableItems.length ? (
            sortedAvailableItems.map((entry) => (
              <div key={entry.item_name} className="entry-row">
                <div className="entry-item">
                  {itemImageMap.get(entry.item_name) ? (
                    <img src={itemImageMap.get(entry.item_name) ?? undefined} alt={entry.item_name} loading="lazy" />
                  ) : null}
                  <span>{entry.item_name}</span>
                </div>
                <input
                  value={entry.quantity}
                  onChange={(event) =>
                    setAvailableItems((state) =>
                      state.map((current) =>
                        current.item_name === entry.item_name ? { ...current, quantity: event.target.value } : current,
                      ),
                    )
                  }
                  placeholder="0.0"
                />
                <button
                  type="button"
                  className="danger"
                  onClick={() =>
                    setAvailableItems((state) => state.filter((current) => current.item_name !== entry.item_name))
                  }
                >
                  x
                </button>
              </div>
            ))
          ) : (
            <p>No available item override.</p>
          )}
        </details>

        <details>
          <summary>Change importance / weight on raw items</summary>
          <div className="entry-column">
            {Object.entries(rawWeights).map(([item, value]) => (
              <div key={item} className="entry-row raw-config-row">
                <div className="entry-item">
                  {itemImageMap.get(item) ? (
                    <img src={itemImageMap.get(item) ?? undefined} alt={item} loading="lazy" />
                  ) : null}
                  <span>{item}</span>
                </div>
                <input
                  value={value}
                  onChange={(event) => setRawWeights((state) => ({ ...state, [item]: event.target.value }))}
                />
              </div>
            ))}
          </div>
        </details>

        <details>
          <summary>Change limit on raw items</summary>
          <div className="entry-column">
            {Object.entries(rawLimits).map(([item, value]) => (
              <div key={item} className="entry-row raw-config-row">
                <div className="entry-item">
                  {itemImageMap.get(item) ? (
                    <img src={itemImageMap.get(item) ?? undefined} alt={item} loading="lazy" />
                  ) : null}
                  <span>{item}</span>
                </div>
                <input
                  value={value}
                  onChange={(event) => setRawLimits((state) => ({ ...state, [item]: event.target.value }))}
                />
              </div>
            ))}
          </div>
        </details>
      </section>

      <section className="panel optimizer-results">
        <header>
          <h2>Optimizer results</h2>
          <span className={`status status-${result?.status?.toLowerCase() ?? "idle"}`}>
            {result?.status ?? "Idle"}
          </span>
        </header>

        {result && result.status !== "Optimal" ? (
          <p>
            Solver status: <strong>{result.status}</strong>. Try adjusting targets/limits.
          </p>
        ) : null}

        {result?.recipes.length ? (
          <div className="recipe-table-wrapper optimizer-recipe-list">
            {result.recipes.map((recipe) => (
              <section key={recipe.recipe_id} className="line-recipe-row">
                <div className="line-flow-row optimizer-line-flow-row">
                  <div className="line-flow-column outputs">
                    <div className="line-flow-items">
                      {recipe.outputs.map((output, index) => (
                        <article key={`${recipe.recipe_id}-out-${output.item_name}-${index}`} className="line-flow-item">
                          {output.image_url ? (
                            <img src={resolveImageSrc(output.image_url)} alt={output.item_name} loading="lazy" />
                          ) : null}
                          <span className="line-flow-item-name">{output.item_name}</span>
                          <span className="line-flow-item-rate">Base: {output.per_building_rate}/min</span>
                          <span className="line-flow-item-rate total">Total: {output.total_rate}/min</span>
                        </article>
                      ))}
                      {!recipe.outputs.length ? <p className="empty">No outputs</p> : null}
                    </div>
                  </div>

                  <div className="line-building-column">
                    <div className="line-building-chip">
                      <span className="line-building-recipe">{recipe.recipe_name}</span>
                      {recipe.building_image_url ? (
                        <img src={resolveImageSrc(recipe.building_image_url)} alt={recipe.building_name} loading="lazy" />
                      ) : null}
                      <strong>{recipe.building_name}</strong>
                      <div className="line-building-meta">
                        <span>Buildings: {formatBuildingCount(recipe.nb_building)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="line-flow-column inputs">
                    <div className="line-flow-items">
                      {recipe.inputs.map((input, index) => (
                        <article key={`${recipe.recipe_id}-in-${input.item_name}-${index}`} className="line-flow-item">
                          {input.image_url ? (
                            <img src={resolveImageSrc(input.image_url)} alt={input.item_name} loading="lazy" />
                          ) : null}
                          <span className="line-flow-item-name">{input.item_name}</span>
                          <span className="line-flow-item-rate">Base: {input.per_building_rate}/min</span>
                          <span className="line-flow-item-rate total">Total: {input.total_rate}/min</span>
                        </article>
                      ))}
                      {!recipe.inputs.length ? <p className="empty">No inputs</p> : null}
                    </div>
                  </div>
                </div>
              </section>
            ))}
          </div>
        ) : (
          <p>No recipe result yet.</p>
        )}

        <div className="optimizer-summary-grid">
          <article>
            <h4>Materials balance</h4>
            <ul>
              {result?.materials.map((material) => (
                <li key={material.item_name}>
                  {material.image_url ? (
                    <img src={resolveImageSrc(material.image_url)} alt={material.item_name} loading="lazy" />
                  ) : null}
                  <span>{material.item_name}</span>
                  <strong>{material.net_rate}/min</strong>
                </li>
              ))}
            </ul>
          </article>

          <article>
            <h4>Buildings needed</h4>
            <ul>
              {result?.buildings.map((building) => (
                <li key={building.building_name}>
                  {building.image_url ? (
                    <img src={resolveImageSrc(building.image_url)} alt={building.building_name} loading="lazy" />
                  ) : null}
                  <span>{building.building_name}</span>
                  <strong>{building.count}</strong>
                </li>
              ))}
            </ul>
          </article>
        </div>

        <div className="graph-wrapper">
          <ReactFlow
            nodes={graph.nodes}
            edges={graph.edges}
            edgeTypes={EDGE_TYPES}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            proOptions={{ hideAttribution: true }}
          >
            <MiniMap />
            <Controls />
            <Background color="#38516e" gap={20} />
          </ReactFlow>
        </div>
      </section>
    </div>
  );
}
