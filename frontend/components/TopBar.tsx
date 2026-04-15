import MarketSelector from './MarketSelector';
import TimeWindowSelector from './TimeWindowSelector';
import PortfolioSelector from './PortfolioSelector';
import ExportButton from './ExportButton';
import ResearchModeSwitch from './ResearchModeSwitch';

export default function TopBar() {
  return (
    <div className="h-16 flex items-center px-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="flex space-x-4">
        <MarketSelector />
        <TimeWindowSelector />
        <PortfolioSelector />
      </div>
      <div className="flex-1" />
      <div className="flex space-x-4">
        <ExportButton />
        <ResearchModeSwitch />
      </div>
    </div>
  );
}