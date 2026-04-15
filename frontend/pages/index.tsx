import { useEffect } from 'react';
import { useRouter } from 'next/router';

/**
 * Default index page
 *
 * Redirects to the market overview page on initial load.  This helps
 * users who navigate to the root URL without specifying a section.
 */
export default function IndexPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/overview');
  }, [router]);
  return null;
}