"use client";

import { useTheme } from "@/components/providers";
import { Card, Field, PageHeader, inputCls } from "@/components/ui";

export default function SettingsPage() {
  const { theme, toggle } = useTheme();
  return (
    <div>
      <PageHeader title="Settings" sub="Profile · appearance · data · research defaults" />
      <div className="grid max-w-3xl grid-cols-1 gap-4">
        <Card>
          <div className="mb-2 text-sm font-semibold">Appearance</div>
          <div className="flex gap-2 text-sm">
            {(["light", "dark"] as const).map((t) => (
              <button
                key={t}
                onClick={() => theme !== t && toggle()}
                className={`rounded-lg border px-4 py-1.5 capitalize ${theme === t ? "border-(--color-ink) font-semibold" : "border-(--color-edge) text-(--color-muted)"}`}
              >
                {t}
              </button>
            ))}
          </div>
        </Card>
        <Card>
          <div className="mb-3 text-sm font-semibold">API</div>
          <Field label="Base URL (NEXT_PUBLIC_API_BASE_URL)">
            <input className={inputCls} readOnly value={process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"} />
          </Field>
          <p className="mt-2 text-xs text-(--color-muted)">Frontend talks only to this backend. No direct database or broker access.</p>
        </Card>
        <Card>
          <div className="mb-3 text-sm font-semibold">Research defaults</div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Default capital"><input className={inputCls} defaultValue={100000} /></Field>
            <Field label="Default cost %"><input className={inputCls} defaultValue={0.1} /></Field>
            <Field label="Risk-free rate %"><input className={inputCls} defaultValue={2} /></Field>
            <Field label="Periods / year"><input className={inputCls} defaultValue={252} /></Field>
          </div>
        </Card>
      </div>
    </div>
  );
}
