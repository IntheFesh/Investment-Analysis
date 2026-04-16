import { useState } from 'react';
import { useRouter } from 'next/router';
import { exportService } from '@/services/exportService';
import { ApiError } from '@/lib/apiTypes';
import { useAppContext } from '@/context/AppContext';

export default function ExportButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { portfolioId } = useAppContext();

  const handleExport = async () => {
    if (loading) return;
    setLoading(true);

    try {
      const page = router.pathname.replace(/^\//, '') || 'overview';
      const data = await exportService.exportPage({
        page,
        portfolio_id: portfolioId,
        formats: ['JSON', 'Markdown', 'CSV', 'PNG'],
      });
      window.alert(`导出任务已提交，下载链接：${data.download_link}`);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : '导出失败，请稍后重试';
      window.alert(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      className="px-3 py-2 text-sm font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
      disabled={loading}
    >
      {loading ? '导出中…' : '导出'}
    </button>
  );
}
