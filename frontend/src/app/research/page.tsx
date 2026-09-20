import Link from "next/link";
import { Badge, Card, PageHeader } from "@/components/ui";

const ROWS = [
  { exp: "BTC SMA 20/50", asset: "BTC-USD", strategy: "SMA", date: "19 Sep", status: "Complete" },
  { exp: "NVDA EMA trend", asset: "NVDA", strategy: "EMA", date: "18 Sep", status: "Complete" },
  { exp: "Portfolio min-vol", asset: "Multi", strategy: "Risk Parity", date: "18 Sep", status: "Complete" },
  { exp: "BTC regime K-Means", asset: "BTC-USD", strategy: "Regime", date: "17 Sep", status: "Complete" },
];

export default function ResearchPage() {
  return (
    <div>
      <PageHeader title="Research" sub="Saved experiments, backtests and reports" />
      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-(--color-muted)">
              <th className="py-2">Experiment</th><th>Asset</th><th>Strategy</th><th>Date</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.exp} className="border-t border-(--color-edge)">
                <td className="py-2.5 font-medium">{r.exp}</td>
                <td>{r.asset}</td><td>{r.strategy}</td><td>{r.date}</td>
                <td><Badge tone="positive">{r.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <p className="mt-3 text-sm">
        <Link href="/backtesting" className="font-medium text-(--color-info)">+ New backtest experiment</Link>
      </p>
    </div>
  );
}
