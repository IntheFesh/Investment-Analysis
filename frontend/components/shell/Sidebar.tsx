import Link from 'next/link';
import { useRouter } from 'next/router';
import clsx from 'clsx';
import { ReactNode } from 'react';

interface NavItem {
  href: string;
  label: string;
  hint?: string;
  icon: ReactNode;
}

const navItems: NavItem[] = [
  {
    href: '/overview',
    label: '市场总览',
    hint: '指数 · 板块 · 资金 · 广度',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <path d="M3 15l4-4 3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M13 7h4v4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: '/sentiment',
    label: '风险情绪',
    hint: '短/中期仪表 + 因子分解',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <path d="M10 3a7 7 0 017 7" strokeLinecap="round" />
        <path d="M3 10a7 7 0 017-7" strokeLinecap="round" />
        <path d="M10 10l4-3" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/portfolio',
    label: '基金组合',
    hint: '穿透 · 诊断 · AI 导出',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <rect x="3" y="5" width="14" height="11" rx="2" />
        <path d="M3 9h14" />
        <path d="M8 5V3h4v2" />
      </svg>
    ),
  },
  {
    href: '/fund',
    label: '单基金研究',
    hint: '净值 · 风控 · 组合关系',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <circle cx="10" cy="10" r="7" />
        <path d="M7 10l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: '/simulation',
    label: '情景模拟',
    hint: '统计 · 情景冲击 · 敏感度',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <path d="M4 17V5h12v12H4z" />
        <path d="M7 13l2-3 2 2 2-4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    href: '/import',
    label: '组合导入',
    hint: '截图 / 代码 / CSV',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <path d="M10 3v10m0 0l-3-3m3 3l3-3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M4 15h12" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    href: '/settings',
    label: '偏好与风险',
    hint: '风险问卷 · 偏好',
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.4">
        <circle cx="10" cy="10" r="2.5" />
        <path d="M10 3v2M10 15v2M3 10h2M15 10h2M5 5l1.4 1.4M13.6 13.6L15 15M5 15l1.4-1.4M13.6 6.4L15 5" strokeLinecap="round" />
      </svg>
    ),
  },
];

export function Sidebar({ collapsed }: { collapsed?: boolean }) {
  const router = useRouter();
  return (
    <aside
      className={clsx(
        'h-screen sticky top-0 bg-surface-raised border-r border-border flex flex-col transition-[width] duration-standard',
        collapsed ? 'w-16' : 'w-60'
      )}
      aria-label="主导航"
    >
      <div className="flex items-center gap-2 h-14 px-4 border-b border-border">
        <div className="h-8 w-8 rounded-md bg-brand/20 text-brand flex items-center justify-center">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M3 15l4-4 3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M13 7h4v4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <div className="text-body-md font-semibold text-text-primary leading-tight">投研工作台</div>
            <div className="text-micro text-text-tertiary leading-tight">Investment Research</div>
          </div>
        )}
      </div>
      <nav className="flex-1 overflow-y-auto p-2 flex flex-col gap-0.5">
        {navItems.map((item) => {
          const active = router.pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? 'page' : undefined}
              className={clsx(
                'group flex items-center gap-3 rounded-md px-2.5 h-9 text-body-sm transition-colors duration-standard',
                active
                  ? 'bg-brand/15 text-text-primary shadow-inset-line'
                  : 'text-text-secondary hover:bg-surface-sunken hover:text-text-primary'
              )}
              title={collapsed ? `${item.label} · ${item.hint ?? ''}` : undefined}
            >
              <span
                className={clsx(
                  'h-5 w-5 shrink-0 flex items-center justify-center',
                  active ? 'text-brand' : 'text-text-tertiary group-hover:text-text-primary'
                )}
              >
                {item.icon}
              </span>
              {!collapsed && (
                <span className="flex-1 flex items-center justify-between gap-2">
                  <span className="font-medium">{item.label}</span>
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border px-4 py-3">
        {!collapsed && (
          <div className="text-micro text-text-tertiary leading-5">
            {new Date().getFullYear()} · 数据延迟以各适配器 meta 为准
          </div>
        )}
      </div>
    </aside>
  );
}
