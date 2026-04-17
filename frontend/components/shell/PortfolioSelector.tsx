import { useAppContext } from '@/context/AppContext';
import { Select } from '@/components/ui/Select';

export function PortfolioSelector() {
  const { portfolioId, setPortfolioId, bootstrapData } = useAppContext();
  const portfolios = bootstrapData?.portfolios ?? [];
  if (portfolios.length === 0) {
    return (
      <Select
        size="sm"
        value={portfolioId}
        onChange={(e) => setPortfolioId(e.target.value)}
        options={[{ value: portfolioId, label: portfolioId }]}
      />
    );
  }
  return (
    <Select
      size="sm"
      value={portfolioId}
      onChange={(e) => setPortfolioId(e.target.value)}
      options={portfolios.map((p) => ({
        value: p.id,
        label: p.is_default ? `${p.label} · 默认` : p.label,
      }))}
    />
  );
}
