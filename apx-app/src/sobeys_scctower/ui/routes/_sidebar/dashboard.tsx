import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import { useGetExecutiveDashboardSuspense } from "@/lib/api";
import { selector } from "@/lib/selector";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import KpiCard from "@/components/sobeys/kpi-card";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export const Route = createFileRoute("/_sidebar/dashboard")({
  component: () => (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContent />
    </Suspense>
  ),
});

function DashboardContent() {
  const { data } = useGetExecutiveDashboardSuspense(selector());

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{data.title}</h1>
        <p className="text-sm text-muted-foreground">{data.subtitle}</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {data.kpi_cards.map((kpi) => (
          <KpiCard key={kpi.id} {...kpi} />
        ))}
      </div>

      {/* Row 2: Demand Forecast + Supplier Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">{data.demand_forecasting.title}</CardTitle>
            <p className="text-xs text-muted-foreground">
              {data.demand_forecasting.accuracy_label}: {data.demand_forecasting.accuracy_value}%
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data.demand_forecasting.chart_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="hsl(142, 42%, 44%)"
                  fill="hsl(142, 42%, 44%)"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">{data.supplier_risk.label}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-8">
            <div
              className={`text-5xl font-bold ${
                data.supplier_risk.value === "Low"
                  ? "text-green-600"
                  : data.supplier_risk.value === "Medium"
                    ? "text-yellow-600"
                    : "text-red-600"
              }`}
            >
              {data.supplier_risk.value}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {data.supplier_risk.change > 0 ? "+" : ""}
              {data.supplier_risk.change}
              {data.supplier_risk.change_unit} vs last period
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Inventory Levels + Supplier Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{data.inventory_levels.title}</CardTitle>
            <p className="text-xs text-muted-foreground">
              Total: {data.inventory_levels.prefix}
              {data.inventory_levels.total_value}
              {data.inventory_levels.unit}
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.inventory_levels.locations} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => `$${v}M`} />
                <Bar dataKey="value" fill="hsl(142, 42%, 44%)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">{data.supplier_performance.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs">Supplier</TableHead>
                  <TableHead className="text-xs text-right">OTD %</TableHead>
                  <TableHead className="text-xs text-right">Quality</TableHead>
                  <TableHead className="text-xs">Lead Time</TableHead>
                  <TableHead className="text-xs">Risk</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.supplier_performance.suppliers.map((s) => (
                  <TableRow key={s.name}>
                    <TableCell className="text-sm font-medium">{s.name}</TableCell>
                    <TableCell className="text-sm text-right">{s.on_time_delivery}%</TableCell>
                    <TableCell className="text-sm text-right">{s.quality_score}%</TableCell>
                    <TableCell className="text-sm">{s.lead_time}</TableCell>
                    <TableCell>
                      <Badge
                        className={
                          s.risk_score === "Low"
                            ? "bg-green-100 text-green-800"
                            : s.risk_score === "Medium"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }
                      >
                        {s.risk_score}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Row 4: Risk Analysis + Logistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {data.predictive_risk_analysis.title}
            </CardTitle>
            <p className="text-xs text-muted-foreground">
              {data.predictive_risk_analysis.period}
            </p>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.predictive_risk_analysis.disruption_types.map((d) => (
              <div key={d.type} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{d.type}</span>
                  <span className="font-medium">{d.probability}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      d.probability >= 70
                        ? "bg-red-500"
                        : d.probability >= 40
                          ? "bg-yellow-500"
                          : "bg-green-500"
                    }`}
                    style={{ width: `${d.probability}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">OTIF Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={data.logistics_transportation.otif_over_time.chart_data}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[80, 100]} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="hsl(145, 72%, 18%)"
                  fill="hsl(145, 72%, 18%)"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-28 rounded-lg" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Skeleton className="lg:col-span-2 h-72 rounded-lg" />
        <Skeleton className="h-72 rounded-lg" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Skeleton className="h-72 rounded-lg" />
        <Skeleton className="h-72 rounded-lg" />
      </div>
    </div>
  );
}
