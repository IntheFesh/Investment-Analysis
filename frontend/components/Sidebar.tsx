import Link from 'next/link';
import { useRouter } from 'next/router';

const navItems = [
  { href: '/overview', label: '市场总览' },
  { href: '/sentiment', label: '风险情绪' },
  { href: '/portfolio', label: '基金组合' },
  { href: '/fund', label: '单基金研究' },
  { href: '/simulation', label: '情景模拟' },
];

export default function Sidebar() {
  const router = useRouter();
  return (
    <aside className="w-48 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="h-16 flex items-center justify-center font-semibold text-lg border-b border-gray-200 dark:border-gray-700">
        投研工作台
      </div>
      <nav className="flex flex-col p-2 space-y-1">
        {navItems.map((item) => {
          const isActive = router.pathname.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href} className={`block px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-800 dark:text-white' : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'}`}> 
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}