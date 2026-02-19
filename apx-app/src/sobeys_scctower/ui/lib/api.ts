import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";

export interface ChartDataPointOut {
  month: string;
  value: number;
}

export interface ChatMessageIn {
  content: string;
  role: string;
}

export interface ChatRequestIn {
  messages: ChatMessageIn[];
}

export interface ChatTaskOut {
  response?: string;
  status: string;
  task_id: string;
}

export interface ComplexValue {
  display?: string | null;
  primary?: boolean | null;
  ref?: string | null;
  type?: string | null;
  value?: string | null;
}

export interface ContributingFactorOut {
  name: string;
  value: number;
}

export interface CustomerLocationOut {
  customer_id: string;
  latitude: number;
  location: string;
  longitude: number;
  name: string;
}

export interface DcInventoryOut {
  allocated_qty: number;
  dc_id: string;
  dc_name: string;
  excess_qty: number;
  product_id: string;
  product_name: string;
  safety_stock: number;
  snapshot_date: string;
  total_qty: number;
}

export interface DemandForecastingSectionOut {
  accuracy_label: string;
  accuracy_value: number;
  chart_data: ChartDataPointOut[];
  period: string;
  title: string;
  unit: string;
}

export interface DisruptionTypeOut {
  probability: number;
  type: string;
}

export interface ExecutiveDashboardOut {
  demand_forecasting: DemandForecastingSectionOut;
  inventory_levels: InventoryLevelsOut;
  kpi_cards: KpiCardOut[];
  logistics_transportation: LogisticsTransportationOut;
  predictive_risk_analysis: PredictiveRiskOut;
  risk_assessment: RiskAssessmentOut;
  subtitle: string;
  supplier_performance: SupplierPerformanceSectionOut;
  supplier_risk: SupplierRiskOut;
  title: string;
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface IncomingSupplyOut {
  destination_dc: string;
  expected_arrival_date: string;
  expected_arrival_days: number;
  product_name: string;
  qty: number;
  shipment_id: string;
  source_location: string;
}

export interface InventoryLevelsOut {
  locations: InventoryLocationOut[];
  period: string;
  prefix: string;
  subtitle: string;
  title: string;
  total_value: number;
  unit: string;
}

export interface InventoryLocationOut {
  name: string;
  value: number;
}

export interface KpiCardOut {
  change?: number;
  change_unit?: string;
  id: string;
  label: string;
  prefix?: string;
  unit?: string;
  value: number;
}

export interface LogisticsMetricOut {
  chart_data: ChartDataPointOut[];
  label: string;
  period: string;
  unit: string;
  value: number;
}

export interface LogisticsTransportationOut {
  expedited_delayed: LogisticsMetricOut;
  otif_over_time: LogisticsMetricOut;
  title: string;
}

export interface Name {
  family_name?: string | null;
  given_name?: string | null;
}

export interface PredictiveRiskOut {
  contributing_factors: ContributingFactorOut[];
  disruption_label: string;
  disruption_level: string;
  disruption_types: DisruptionTypeOut[];
  period: string;
  title: string;
}

export interface RiskAssessmentOut {
  factors: RiskFactorOut[];
  title: string;
}

export interface RiskFactorOut {
  factor: string;
  severity: string;
}

export interface ShippingScheduleOut {
  customer_name: string;
  dc_name: string;
  product_name: string;
  qty: number;
  schedule_date: string;
  schedule_id: string;
}

export interface StockoutRiskOut {
  current_qty: number;
  days_of_supply: number;
  dc_name: string;
  product_name: string;
  risk_level: string;
  safety_stock: number;
}

export interface StorageLocationOut {
  latitude: number;
  location: string;
  location_id: string;
  location_name: string;
  longitude: number;
  type: string;
}

export interface SupplierOrderOut {
  expected_arrival_date: string;
  expected_arrival_days: number;
  order_id: string;
  product_name: string;
  qty: number;
  supplier_name: string;
}

export interface SupplierPerformanceOut {
  lead_time: string;
  name: string;
  on_time_delivery: number;
  quality_score: number;
  risk_score: string;
}

export interface SupplierPerformanceSectionOut {
  columns: string[];
  suppliers: SupplierPerformanceOut[];
  title: string;
}

export interface SupplierRiskOut {
  change: number;
  change_unit: string;
  label: string;
  value: string;
}

export interface User {
  active?: boolean | null;
  display_name?: string | null;
  emails?: ComplexValue[] | null;
  entitlements?: ComplexValue[] | null;
  external_id?: string | null;
  groups?: ComplexValue[] | null;
  id?: string | null;
  name?: Name | null;
  roles?: ComplexValue[] | null;
  schemas?: UserSchema[] | null;
  user_name?: string | null;
}

export const UserSchema = {
  "urn:ietf:params:scim:schemas:core:2.0:User": "urn:ietf:params:scim:schemas:core:2.0:User",
  "urn:ietf:params:scim:schemas:extension:workspace:2.0:User": "urn:ietf:params:scim:schemas:extension:workspace:2.0:User",
} as const;

export type UserSchema = (typeof UserSchema)[keyof typeof UserSchema];

export interface ValidationError {
  ctx?: Record<string, unknown>;
  input?: unknown;
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface VersionOut {
  version: string;
}

export interface PollChatParams {
  task_id: string;
}

export interface CurrentUserParams {
  "X-Forwarded-Access-Token"?: string | null;
}

export interface ListDcInventoryParams {
  dc_id?: string | null;
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export const pollChat = async (params: PollChatParams, options?: RequestInit): Promise<{ data: ChatTaskOut }> => {
  const res = await fetch(`/api/chat/poll/${params.task_id}`, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const pollChatKey = (params?: PollChatParams) => {
  return ["/api/chat/poll/{task_id}", params] as const;
};

export function usePollChat<TData = { data: ChatTaskOut }>(options: { params: PollChatParams; query?: Omit<UseQueryOptions<{ data: ChatTaskOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: pollChatKey(options.params), queryFn: () => pollChat(options.params), ...options?.query });
}

export function usePollChatSuspense<TData = { data: ChatTaskOut }>(options: { params: PollChatParams; query?: Omit<UseSuspenseQueryOptions<{ data: ChatTaskOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: pollChatKey(options.params), queryFn: () => pollChat(options.params), ...options?.query });
}

export const startChat = async (data: ChatRequestIn, options?: RequestInit): Promise<{ data: ChatTaskOut }> => {
  const res = await fetch("/api/chat/start", { ...options, method: "POST", headers: { "Content-Type": "application/json", ...options?.headers }, body: JSON.stringify(data) });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export function useStartChat(options?: { mutation?: UseMutationOptions<{ data: ChatTaskOut }, ApiError, ChatRequestIn> }) {
  return useMutation({ mutationFn: (data) => startChat(data), ...options?.mutation });
}

export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{ data: User }> => {
  const res = await fetch("/api/current-user", { ...options, method: "GET", headers: { ...(params?.["X-Forwarded-Access-Token"] != null && { "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"] }), ...options?.headers } });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const currentUserKey = (params?: CurrentUserParams) => {
  return ["/api/current-user", params] as const;
};

export function useCurrentUser<TData = { data: User }>(options?: { params?: CurrentUserParams; query?: Omit<UseQueryOptions<{ data: User }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export function useCurrentUserSuspense<TData = { data: User }>(options?: { params?: CurrentUserParams; query?: Omit<UseSuspenseQueryOptions<{ data: User }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: currentUserKey(options?.params), queryFn: () => currentUser(options?.params), ...options?.query });
}

export const listCustomerLocations = async (options?: RequestInit): Promise<{ data: CustomerLocationOut[] }> => {
  const res = await fetch("/api/customer-locations", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listCustomerLocationsKey = () => {
  return ["/api/customer-locations"] as const;
};

export function useListCustomerLocations<TData = { data: CustomerLocationOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: CustomerLocationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listCustomerLocationsKey(), queryFn: () => listCustomerLocations(), ...options?.query });
}

export function useListCustomerLocationsSuspense<TData = { data: CustomerLocationOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: CustomerLocationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listCustomerLocationsKey(), queryFn: () => listCustomerLocations(), ...options?.query });
}

export const getExecutiveDashboard = async (options?: RequestInit): Promise<{ data: ExecutiveDashboardOut }> => {
  const res = await fetch("/api/dashboard/executive", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const getExecutiveDashboardKey = () => {
  return ["/api/dashboard/executive"] as const;
};

export function useGetExecutiveDashboard<TData = { data: ExecutiveDashboardOut }>(options?: { query?: Omit<UseQueryOptions<{ data: ExecutiveDashboardOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: getExecutiveDashboardKey(), queryFn: () => getExecutiveDashboard(), ...options?.query });
}

export function useGetExecutiveDashboardSuspense<TData = { data: ExecutiveDashboardOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: ExecutiveDashboardOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: getExecutiveDashboardKey(), queryFn: () => getExecutiveDashboard(), ...options?.query });
}

export const listDcInventory = async (params?: ListDcInventoryParams, options?: RequestInit): Promise<{ data: DcInventoryOut[] }> => {
  const searchParams = new URLSearchParams();
  if (params?.dc_id != null) searchParams.set("dc_id", String(params?.dc_id));
  const queryString = searchParams.toString();
  const url = queryString ? `/api/dc-inventory?${queryString}` : `/api/dc-inventory`;
  const res = await fetch(url, { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listDcInventoryKey = (params?: ListDcInventoryParams) => {
  return ["/api/dc-inventory", params] as const;
};

export function useListDcInventory<TData = { data: DcInventoryOut[] }>(options?: { params?: ListDcInventoryParams; query?: Omit<UseQueryOptions<{ data: DcInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listDcInventoryKey(options?.params), queryFn: () => listDcInventory(options?.params), ...options?.query });
}

export function useListDcInventorySuspense<TData = { data: DcInventoryOut[] }>(options?: { params?: ListDcInventoryParams; query?: Omit<UseSuspenseQueryOptions<{ data: DcInventoryOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listDcInventoryKey(options?.params), queryFn: () => listDcInventory(options?.params), ...options?.query });
}

export const listIncomingSupply = async (options?: RequestInit): Promise<{ data: IncomingSupplyOut[] }> => {
  const res = await fetch("/api/incoming-supply", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listIncomingSupplyKey = () => {
  return ["/api/incoming-supply"] as const;
};

export function useListIncomingSupply<TData = { data: IncomingSupplyOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: IncomingSupplyOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listIncomingSupplyKey(), queryFn: () => listIncomingSupply(), ...options?.query });
}

export function useListIncomingSupplySuspense<TData = { data: IncomingSupplyOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: IncomingSupplyOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listIncomingSupplyKey(), queryFn: () => listIncomingSupply(), ...options?.query });
}

export const listShippingSchedule = async (options?: RequestInit): Promise<{ data: ShippingScheduleOut[] }> => {
  const res = await fetch("/api/shipping-schedule", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listShippingScheduleKey = () => {
  return ["/api/shipping-schedule"] as const;
};

export function useListShippingSchedule<TData = { data: ShippingScheduleOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: ShippingScheduleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listShippingScheduleKey(), queryFn: () => listShippingSchedule(), ...options?.query });
}

export function useListShippingScheduleSuspense<TData = { data: ShippingScheduleOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: ShippingScheduleOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listShippingScheduleKey(), queryFn: () => listShippingSchedule(), ...options?.query });
}

export const listStockoutRisk = async (options?: RequestInit): Promise<{ data: StockoutRiskOut[] }> => {
  const res = await fetch("/api/stockout-risk", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listStockoutRiskKey = () => {
  return ["/api/stockout-risk"] as const;
};

export function useListStockoutRisk<TData = { data: StockoutRiskOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: StockoutRiskOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listStockoutRiskKey(), queryFn: () => listStockoutRisk(), ...options?.query });
}

export function useListStockoutRiskSuspense<TData = { data: StockoutRiskOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: StockoutRiskOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listStockoutRiskKey(), queryFn: () => listStockoutRisk(), ...options?.query });
}

export const listStorageLocations = async (options?: RequestInit): Promise<{ data: StorageLocationOut[] }> => {
  const res = await fetch("/api/storage-locations", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listStorageLocationsKey = () => {
  return ["/api/storage-locations"] as const;
};

export function useListStorageLocations<TData = { data: StorageLocationOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: StorageLocationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listStorageLocationsKey(), queryFn: () => listStorageLocations(), ...options?.query });
}

export function useListStorageLocationsSuspense<TData = { data: StorageLocationOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: StorageLocationOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listStorageLocationsKey(), queryFn: () => listStorageLocations(), ...options?.query });
}

export const listSupplierOrders = async (options?: RequestInit): Promise<{ data: SupplierOrderOut[] }> => {
  const res = await fetch("/api/supplier-orders", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const listSupplierOrdersKey = () => {
  return ["/api/supplier-orders"] as const;
};

export function useListSupplierOrders<TData = { data: SupplierOrderOut[] }>(options?: { query?: Omit<UseQueryOptions<{ data: SupplierOrderOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: listSupplierOrdersKey(), queryFn: () => listSupplierOrders(), ...options?.query });
}

export function useListSupplierOrdersSuspense<TData = { data: SupplierOrderOut[] }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: SupplierOrderOut[] }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: listSupplierOrdersKey(), queryFn: () => listSupplierOrders(), ...options?.query });
}

export const version = async (options?: RequestInit): Promise<{ data: VersionOut }> => {
  const res = await fetch("/api/version", { ...options, method: "GET" });
  if (!res.ok) {
    const body = await res.text();
    let parsed: unknown;
    try { parsed = JSON.parse(body); } catch { parsed = body; }
    throw new ApiError(res.status, res.statusText, parsed);
  }
  return { data: await res.json() };
};

export const versionKey = () => {
  return ["/api/version"] as const;
};

export function useVersion<TData = { data: VersionOut }>(options?: { query?: Omit<UseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

export function useVersionSuspense<TData = { data: VersionOut }>(options?: { query?: Omit<UseSuspenseQueryOptions<{ data: VersionOut }, ApiError, TData>, "queryKey" | "queryFn"> }) {
  return useSuspenseQuery({ queryKey: versionKey(), queryFn: () => version(), ...options?.query });
}

