import { createFileRoute } from "@tanstack/react-router";
import { Suspense } from "react";
import {
  useListDcInventorySuspense,
  useListIncomingSupplySuspense,
  useListStockoutRiskSuspense,
  useListShippingScheduleSuspense,
} from "@/lib/api";
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

const DASHBOARD_URL =
  "https://adb-7405613286317055.15.azuredatabricks.net/embed/dashboardsv3/01f10dccfe351d79a3e9c299679cd195";

export const Route = createFileRoute("/_sidebar/dc-network")({
  component: () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Distribution Centres</h1>
        <p className="text-sm text-muted-foreground">
          Distribution centre inventory, incoming supply, and stockout risk
          analysis
        </p>
      </div>

      {/* Embedded AI/BI Dashboard */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Distribution Network Overview
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Interactive geospatial dashboard powered by Databricks AI/BI
          </p>
        </CardHeader>
        <CardContent className="p-0">
          <iframe
            src={DASHBOARD_URL}
            className="w-full border-0 rounded-b-lg"
            style={{ height: "420px" }}
            title="DC Network Geospatial Overview"
            allow="fullscreen"
          />
        </CardContent>
      </Card>

      {/* Stockout Risk */}
      <Suspense fallback={<Skeleton className="h-72 rounded-lg" />}>
        <StockoutRiskSection />
      </Suspense>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Suspense fallback={<Skeleton className="h-96 rounded-lg" />}>
          <DcInventorySection />
        </Suspense>
        <Suspense fallback={<Skeleton className="h-96 rounded-lg" />}>
          <IncomingSupplySection />
        </Suspense>
      </div>

      <Suspense fallback={<Skeleton className="h-72 rounded-lg" />}>
        <ShippingScheduleSection />
      </Suspense>
    </div>
  ),
});

function StockoutRiskSection() {
  const { data: risks } = useListStockoutRiskSuspense(selector());
  const riskColor = (level: string) =>
    level === "Critical"
      ? "bg-red-100 text-red-800"
      : level === "High"
        ? "bg-orange-100 text-orange-800"
        : level === "Medium"
          ? "bg-yellow-100 text-yellow-800"
          : "bg-green-100 text-green-800";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Stockout Risk Analysis</CardTitle>
        <p className="text-xs text-muted-foreground">
          Top 10 products by days-of-supply risk
        </p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Product</TableHead>
              <TableHead className="text-xs">DC</TableHead>
              <TableHead className="text-xs text-right">On Hand</TableHead>
              <TableHead className="text-xs text-right">
                Safety Stock
              </TableHead>
              <TableHead className="text-xs text-right">
                Days of Supply
              </TableHead>
              <TableHead className="text-xs">Risk</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {risks.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground"
                >
                  Loading data from warehouse...
                </TableCell>
              </TableRow>
            ) : (
              risks.map((r, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm font-medium">
                    {r.product_name}
                  </TableCell>
                  <TableCell className="text-sm">{r.dc_name}</TableCell>
                  <TableCell className="text-sm text-right">
                    {r.current_qty.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {r.safety_stock.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {r.days_of_supply}
                  </TableCell>
                  <TableCell>
                    <Badge className={riskColor(r.risk_level)}>
                      {r.risk_level}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function DcInventorySection() {
  const { data: inventory } = useListDcInventorySuspense(selector());
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">DC Inventory Levels</CardTitle>
        <p className="text-xs text-muted-foreground">
          Top 10 by quantity
        </p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">DC</TableHead>
              <TableHead className="text-xs">Product</TableHead>
              <TableHead className="text-xs text-right">Total Qty</TableHead>
              <TableHead className="text-xs text-right">Allocated</TableHead>
              <TableHead className="text-xs text-right">Excess</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inventory.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground"
                >
                  Loading...
                </TableCell>
              </TableRow>
            ) : (
              inventory.map((item, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm">{item.dc_name}</TableCell>
                  <TableCell className="text-sm">
                    {item.product_name}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {item.total_qty.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {item.allocated_qty.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {item.excess_qty.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function IncomingSupplySection() {
  const { data: supply } = useListIncomingSupplySuspense(selector());
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Incoming Supply Pipeline</CardTitle>
        <p className="text-xs text-muted-foreground">
          Top 10 by arrival time
        </p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Product</TableHead>
              <TableHead className="text-xs">From</TableHead>
              <TableHead className="text-xs">To DC</TableHead>
              <TableHead className="text-xs text-right">Qty</TableHead>
              <TableHead className="text-xs text-right">ETA (days)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {supply.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground"
                >
                  Loading...
                </TableCell>
              </TableRow>
            ) : (
              supply.map((s, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm">{s.product_name}</TableCell>
                  <TableCell className="text-sm">
                    {s.source_location}
                  </TableCell>
                  <TableCell className="text-sm">
                    {s.destination_dc}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    {s.qty.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-sm text-right">
                    <Badge
                      variant="outline"
                      className={
                        s.expected_arrival_days <= 2
                          ? "border-green-500 text-green-700"
                          : s.expected_arrival_days <= 5
                            ? "border-yellow-500 text-yellow-700"
                            : "border-red-500 text-red-700"
                      }
                    >
                      {s.expected_arrival_days}d
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function ShippingScheduleSection() {
  const { data: schedule } = useListShippingScheduleSuspense(selector());
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Outbound Shipping Schedule</CardTitle>
        <p className="text-xs text-muted-foreground">
          Next 10 scheduled shipments
        </p>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-xs">Date</TableHead>
              <TableHead className="text-xs">Product</TableHead>
              <TableHead className="text-xs">DC</TableHead>
              <TableHead className="text-xs">Customer</TableHead>
              <TableHead className="text-xs text-right">Qty</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {schedule.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="text-center text-muted-foreground"
                >
                  Loading...
                </TableCell>
              </TableRow>
            ) : (
              schedule.map((s, i) => (
                <TableRow key={i}>
                  <TableCell className="text-sm">{s.schedule_date}</TableCell>
                  <TableCell className="text-sm">{s.product_name}</TableCell>
                  <TableCell className="text-sm">{s.dc_name}</TableCell>
                  <TableCell className="text-sm">{s.customer_name}</TableCell>
                  <TableCell className="text-sm text-right">
                    {s.qty.toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
