import { Card, CardContent } from "@/components/ui/card";
import { ArrowUp, ArrowDown } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: number;
  unit: string;
  prefix: string;
  change: number;
  change_unit: string;
}

export default function KpiCard({
  label,
  value,
  unit,
  prefix,
  change,
  change_unit,
}: KpiCardProps) {
  const isPositive = change >= 0;
  return (
    <Card className="border-l-4 border-l-primary">
      <CardContent className="pt-5 pb-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </p>
        <p className="text-3xl font-bold mt-1 text-foreground">
          {prefix}
          {value}
          {unit}
        </p>
        <div
          className={`flex items-center gap-1 mt-2 text-sm font-medium ${isPositive ? "text-green-600" : "text-red-500"}`}
        >
          {isPositive ? <ArrowUp size={14} /> : <ArrowDown size={14} />}
          <span>
            {isPositive ? "+" : ""}
            {change}
            {change_unit}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
