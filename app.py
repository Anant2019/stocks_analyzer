import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScreenerHeader } from "@/components/ScreenerHeader";
import { StrategyInfo } from "@/components/StrategyInfo";
import { ResultsTable } from "@/components/ResultsTable";
import { NSE_200_STOCKS } from "@/lib/nse200";
import { generateDemoData, ScreenerResult } from "@/lib/screener";
import { Play, Info } from "lucide-react";

const Index = () => {
  const [results, setResults] = useState<ScreenerResult[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [showStrategy, setShowStrategy] = useState(false);
  const [hasScanned, setHasScanned] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    setResults([]);
    setScanProgress(0);
    setHasScanned(true);

    // Simulate scanning with demo data (replace with real API later)
    for (let i = 0; i <= 100; i += 5) {
      await new Promise((r) => setTimeout(r, 60));
      setScanProgress(i);
    }

    const demoResults = generateDemoData();
    setResults(demoResults);
    setIsScanning(false);
    setScanProgress(100);
  };

  return (
    <div className="min-h-screen bg-background">
      <ScreenerHeader
        totalStocks={NSE_200_STOCKS.length}
        matchCount={results.length}
        isScanning={isScanning}
        scanProgress={scanProgress}
      />

      <div className="px-6 py-4 flex items-center gap-3">
        <Button
          onClick={handleScan}
          disabled={isScanning}
          className="gap-2 font-semibold"
          size="lg"
        >
          <Play className="h-4 w-4" />
          {isScanning ? "Scanning..." : "Scan Now"}
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => setShowStrategy(!showStrategy)}
          className="gap-2"
        >
          <Info className="h-4 w-4" />
          Strategy
        </Button>
        {hasScanned && !isScanning && (
          <span className="ml-auto text-xs text-muted-foreground font-mono">
            Last scan: {new Date().toLocaleTimeString()} · Demo data
          </span>
        )}
      </div>

      {showStrategy && <StrategyInfo />}

      <div className="px-6 pb-6">
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <ResultsTable results={results} />
        </div>
      </div>

      {!hasScanned && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mb-4 glow-bullish">
            <Play className="h-6 w-6 text-bullish" />
          </div>
          <p className="text-lg font-medium">Ready to Scan</p>
          <p className="text-sm mt-1">Analyze NSE 200 stocks for swing buy signals</p>
          <p className="text-xs mt-3 font-mono text-muted-foreground/60">
            Currently showing demo data · Connect live API for real-time screening
          </p>
        </div>
      )}
    </div>
  );
};

export default Index;
