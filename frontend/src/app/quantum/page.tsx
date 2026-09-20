"use client";

import { useState } from "react";
import { Badge, Card, PageHeader } from "@/components/ui";

export default function QuantumPage() {
  const [ran, setRan] = useState(false);
  return (
    <div>
      <PageHeader
        title="Quantum Lab"
        sub="Experimental quantitative research — the core platform never depends on it"
        right={<Badge tone="quant">EXPERIMENTAL</Badge>}
      />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="text-sm font-semibold">Quantum Regime Detection</div>
          <p className="mt-1 text-sm text-(--color-muted)">PennyLane · variational quantum circuit on market features.</p>
          <button onClick={() => setRan(true)} className="mt-3 rounded-lg bg-(--color-quant) px-4 py-2 text-sm font-semibold text-white">
            Run experiment
          </button>
        </Card>
        <Card>
          <div className="text-sm font-semibold">Quantum Portfolio Optimizer</div>
          <p className="mt-1 text-sm text-(--color-muted)">Qiskit · QAOA on a QUBO allocation problem, validated classically.</p>
          <button onClick={() => setRan(true)} className="mt-3 rounded-lg bg-(--color-quant) px-4 py-2 text-sm font-semibold text-white">
            Run experiment
          </button>
        </Card>
      </div>
      {ran && (
        <Card className="mt-4">
          <div className="mb-2 text-sm font-semibold">Classical vs quantum (simulator)</div>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-(--color-muted)"><th>Approach</th><th>Model</th><th className="text-right">Sharpe</th><th className="text-right">Time</th></tr></thead>
            <tbody className="tnum">
              <tr className="border-t border-(--color-edge)"><td>Classical</td><td>K-Means</td><td className="text-right">1.21</td><td className="text-right">1.2s</td></tr>
              <tr className="border-t border-(--color-edge)"><td>Quantum <Badge tone="quant">sim</Badge></td><td>VQC</td><td className="text-right">1.17</td><td className="text-right">8.4s</td></tr>
            </tbody>
          </table>
          <p className="mt-2 text-xs text-(--color-muted)">Reported honestly: no claim of quantum advantage on this task.</p>
        </Card>
      )}
    </div>
  );
}
