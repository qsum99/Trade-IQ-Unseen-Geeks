import {
  ASSETS,
  corrMatrix,
  getHistory,
  rollingCorr,
  searchAssets,
} from "./frontend/src/lib/mock-data.ts";

let failures = 0;
const check = (name, cond, extra = "") => {
  console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra}`);
  if (!cond) failures++;
};

// 1. New index assets exist with metadata
const ixic = ASSETS.find((a) => a.symbol === "^IXIC");
const gspc = ASSETS.find((a) => a.symbol === "^GSPC");
check("^IXIC registered as US Index (NASDAQ/yahoo/USD)", !!ixic && ixic.assetClass === "Index" && ixic.region === "US" && ixic.exchange === "NASDAQ" && ixic.provider === "yahoo" && ixic.currency === "USD");
check("^GSPC registered as US Index (SNP/yahoo/USD)", !!gspc && gspc.assetClass === "Index" && gspc.region === "US" && gspc.provider === "yahoo" && gspc.currency === "USD");
check("8 assets total", ASSETS.length === 8, ` (found ${ASSETS.length})`);

// 2. Search resolves nasdaq / snp
const nasdaq = searchAssets("nasdaq", []);
check('search "nasdaq" finds ^IXIC', nasdaq.some((a) => a.symbol === "^IXIC"), ` (${nasdaq.map((a) => a.symbol)})`);
const snp = searchAssets("snp", []);
check('search "snp" finds ^GSPC', snp.some((a) => a.symbol === "^GSPC"), ` (${snp.map((a) => a.symbol)})`);
check('search "s&p 500" finds ^GSPC', searchAssets("s&p 500", []).some((a) => a.symbol === "^GSPC"));
check("search excludes already-selected", searchAssets("usd", ["BTC-USD"]).every((a) => a.symbol !== "BTC-USD"));

// 3. History generation valid for new symbols
for (const s of ["^IXIC", "^GSPC"]) {
  const h = getHistory(s, 60);
  const okLen = h.length === 60;
  const okOhlc = h.every((b) => b.high >= Math.max(b.open, b.close) && b.low <= Math.min(b.open, b.close) && b.volume > 0);
  const okDates = h.every((b, i) => i === 0 || b.date > h[i - 1].date);
  check(`history ${s}: 60 bars, valid OHLC, ascending dates`, okLen && okOhlc && okDates);
}

// 4. Matrix math includes new symbols
const syms = ["BTC-USD", "GC=F", "NVDA", "^NSEI", "^IXIC", "^GSPC"];
const m = corrMatrix(syms);
check("6x6 matrix", m.matrix.length === 6 && m.matrix.every((r) => r.length === 6));
check("diagonal is 1.00", m.matrix.every((r, i) => r[i] === 1));
check(
  "off-diagonal in [-1,1], no NaN",
  m.matrix.flat().every((v) => typeof v === "number" && !Number.isNaN(v) && v >= -1 && v <= 1),
);
console.log("MATRIX:", JSON.stringify(m.matrix.map((r) => r.map((v) => v.toFixed(2)))));

// 5. Rolling correlation with new symbols
const roll = rollingCorr("^IXIC", "^GSPC", 60);
check("rolling IXIC↔GSPC non-empty, values in range", roll.length > 0 && roll.every((p) => p.value >= -1 && p.value <= 1), ` (${roll.length} points)`);

console.log(failures === 0 ? "\nALL CHECKS PASSED" : `\n${failures} CHECK(S) FAILED`);
process.exit(failures === 0 ? 0 : 1);
