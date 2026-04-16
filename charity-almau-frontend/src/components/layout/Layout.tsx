import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import MobileNav from './MobileNav';
import styles from './Layout.module.css';

const NO_FOOTER_ROUTES = ['/chats'];

export default function Layout() {
  const { pathname } = useLocation();
  const hideFooter = NO_FOOTER_ROUTES.some((r) => pathname.startsWith(r));

  return (
    <div className={styles.layout}>
      <Header />
      <main className={styles.main}>
        <Outlet />
      </main>
      {!hideFooter && <Footer />}
      <MobileNav />
    </div>
  );
}
