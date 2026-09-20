"use client";

import dynamic from "next/dynamic";
import type { PlotParams } from "react-plotly.js";
import { useTheme } from "@/components/providers";

const PlotlyPlot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center">
      <div className="h-32 w-full animate-pulse rounded-lg bg-(--color-elev)" />
    </div>
  ),
});

type Props = {
  height?: number;
  data?: PlotParams["data"];
  layout?: Record<string, unknown>;
  config?: Record<string, unknown>;
};

/** Theme-aware Plotly wrapper — thin lines, minimal grid, crosshair + zoom. */
export function Plot({ height = 320, data = [], layout, config }: Props) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const grid = dark ? "#242830" : "#E6E8EC";
  const ink = dark ? "#F5F7FA" : "#111318";
  const muted = dark ? "#98A2B3" : "#667085";

  return (
    <PlotlyPlot
      data={data}
      layout={{
        autosize: true,
        height,
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { family: "Inter, Geist, sans-serif", size: 11, color: muted },
        margin: { l: 52, r: 12, t: 12, b: 36 },
        xaxis: {
          gridcolor: grid,
          zerolinecolor: grid,
          tickfont: { color: muted },
          rangeslider: { visible: false },
        },
        yaxis: { gridcolor: grid, zerolinecolor: grid, tickfont: { color: muted } },
        hovermode: "x unified",
        hoverlabel: { bgcolor: dark ? "#161A20" : "#FFFFFF", font: { color: ink } },
        showlegend: true,
        legend: { orientation: "h", y: 1.08, font: { color: muted } },
        ...(layout ?? {}),
      }}
      config={{ displaylogo: false, responsive: true, displayModeBar: "hover", ...(config ?? {}) }}
      useResizeHandler
      style={{ width: "100%" }}
    />
  );
}
