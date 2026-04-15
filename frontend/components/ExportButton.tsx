import { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/router';

/**
 * ExportButton component
 *
 * This button triggers an export of the currently viewed page.  It
 * infers the page name from the router pathname (e.g. '/overview' =>
 * 'overview') and posts to the export API.  When the request
 * completes it displays a simple alert with the returned download
 * link.  A more complete implementation could present a modal with
 * format selection and progress feedback.
 */
export default function ExportButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    if (loading) return;
    setLoading(true);
    try {
      // Determine the page name by stripping the leading slash
      const page = router.pathname.replace(/^\//, '') || 'overview';
      const res = await axios.post('/api/v1/export/page', {
        page,
        portfolio_id: null,
        formats: ['JSON', 'Markdown', 'CSV', 'PNG'],
      });
      const { download_link } = res.data.data;
      // For demonstration, simply alert the link; in a real app you'd
      // present a toast or start a download.
      window.alert(`导出任务已提交，下载链接：${download_link}`);
    } catch (err) {
      console.error(err);
      window.alert('导出失败，请稍后重试');
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