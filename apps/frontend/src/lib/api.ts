import axios, { AxiosError } from "axios";

import type {
  ApiErrorPayload,
  Area,
  Balance,
  Building,
  ConflictResponse,
  Factory,
  Item,
  Line,
  OptimizerRequest,
  OptimizerResult,
  Recipe,
  Scenario,
} from "./types";

function trimTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function normalizeApiBase(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) return "";
  return trimTrailingSlash(trimmed);
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE ? `${API_BASE}/api/v1` : "/api/v1",
  timeout: 45000,
});

export function extractApiError(error: unknown): ApiErrorPayload {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as ApiErrorPayload | undefined;
    if (payload) {
      return {
        trace_id: payload.trace_id,
        error_type: payload.error_type,
        message: payload.message ?? payload.detail ?? error.message,
        stack: payload.stack,
        context: payload.context,
      };
    }
    return { message: error.message };
  }
  if (error instanceof Error) {
    return { message: error.message, stack: error.stack };
  }
  return { message: "Unknown error" };
}

export function isConflictError(error: unknown): ConflictResponse | null {
  if (!axios.isAxiosError(error)) return null;
  if (error.response?.status !== 409) return null;
  return error.response.data as ConflictResponse;
}

export async function getHealth() {
  return (await apiClient.get("/health")).data;
}

export async function listItems(): Promise<Item[]> {
  return (await apiClient.get("/meta/items")).data;
}

export async function listBuildings(): Promise<Building[]> {
  return (await apiClient.get("/meta/buildings")).data;
}

export async function listRecipes(maxTier?: number): Promise<Recipe[]> {
  return (await apiClient.get("/meta/recipes", { params: maxTier === undefined ? undefined : { max_tier: maxTier } })).data;
}

export async function listScenarios(includeDeleted = false): Promise<Scenario[]> {
  return (await apiClient.get("/scenarios", { params: { include_deleted: includeDeleted } })).data;
}

export async function createScenario(name: string): Promise<Scenario> {
  return (await apiClient.post("/scenarios", { name })).data;
}

export async function updateScenario(scenarioId: number, payload: { name?: string; is_deleted?: boolean; restore?: boolean }) {
  return (await apiClient.patch(`/scenarios/${scenarioId}`, payload)).data as Scenario;
}

export async function deleteScenario(scenarioId: number) {
  await apiClient.delete(`/scenarios/${scenarioId}`);
}

export async function listAreas(scenarioId: number): Promise<Area[]> {
  return (await apiClient.get(`/scenarios/${scenarioId}/areas`)).data;
}

export async function createArea(scenarioId: number, payload: { name: string; sort_order?: number }): Promise<Area> {
  return (await apiClient.post(`/scenarios/${scenarioId}/areas`, payload)).data;
}

export async function updateArea(areaId: number, payload: { name?: string; sort_order?: number }): Promise<Area> {
  return (await apiClient.patch(`/areas/${areaId}`, payload)).data;
}

export async function deleteArea(areaId: number) {
  await apiClient.delete(`/areas/${areaId}`);
}

export async function listFactories(scenarioId: number, areaId?: number): Promise<Factory[]> {
  return (await apiClient.get(`/scenarios/${scenarioId}/factories`, { params: areaId ? { area_id: areaId } : undefined })).data;
}

export async function createFactory(
  scenarioId: number,
  payload: { area_id: number; name: string; sort_order?: number },
): Promise<Factory> {
  return (await apiClient.post(`/scenarios/${scenarioId}/factories`, payload)).data;
}

export async function updateFactory(
  factoryId: number,
  payload: { area_id?: number; name?: string; sort_order?: number },
): Promise<Factory> {
  return (await apiClient.patch(`/factories/${factoryId}`, payload)).data;
}

export async function deleteFactory(factoryId: number) {
  await apiClient.delete(`/factories/${factoryId}`);
}

export async function listLines(scenarioId: number, areaId?: number, factoryId?: number): Promise<Line[]> {
  return (
    await apiClient.get(`/scenarios/${scenarioId}/lines`, {
      params: {
        ...(areaId ? { area_id: areaId } : {}),
        ...(factoryId ? { factory_id: factoryId } : {}),
      },
    })
  ).data;
}

export async function createLine(
  scenarioId: number,
  payload: {
    area_id: number;
    factory_id: number | null;
    name: string;
    recipe_id: number;
    building_count: number;
    efficiency_multiplier: string;
  },
): Promise<Line> {
  return (await apiClient.post(`/scenarios/${scenarioId}/lines`, payload)).data;
}

export async function updateLine(
  lineId: number,
  payload: {
    version: number;
    area_id?: number;
    factory_id?: number | null;
    name?: string;
    recipe_id?: number;
    building_count?: number;
    efficiency_multiplier?: string;
  },
): Promise<Line> {
  return (await apiClient.patch(`/lines/${lineId}`, payload)).data;
}

export async function deleteLine(lineId: number, version: number): Promise<void> {
  await apiClient.delete(`/lines/${lineId}`, { data: { version } });
}

export async function getBalances(scenarioId: number, areaId?: number, factoryId?: number): Promise<Balance> {
  return (
    await apiClient.get(`/scenarios/${scenarioId}/balances`, {
      params: {
        ...(areaId ? { area_id: areaId } : {}),
        ...(factoryId ? { factory_id: factoryId } : {}),
      },
    })
  ).data;
}

export async function solveOptimizer(payload: OptimizerRequest): Promise<OptimizerResult> {
  return (await apiClient.post(`/optimizer/solve`, payload)).data;
}

export async function getErrorDetails(traceId: string): Promise<ApiErrorPayload> {
  return (await apiClient.get(`/errors/${traceId}`)).data;
}

export function apiBaseUrl(): string {
  return API_BASE;
}

export type ApiAxiosError = AxiosError<ApiErrorPayload>;
