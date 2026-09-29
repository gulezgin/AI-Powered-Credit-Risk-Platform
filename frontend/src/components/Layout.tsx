import { Outlet } from "react-router-dom";
import TopNav from "./TopNav";
import { useI18n } from "../i18n";
import { API_BASE_URL } from "../api/client";

export default function Layout() {
  const { t } = useI18n();

  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <main className="flex-1">
        <div className="mx-auto max-w-[1240px] px-6 py-10">
          <Outlet />
        </div>
      </main>

      <footer className="mt-8 border-t border-rule">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center justify-between gap-3 px-6 py-6">
          <p className="t-small text-ink-3">{t("footer.line")}</p>
          <p className="t-micro fig text-ink-4">{API_BASE_URL}</p>
        </div>
      </footer>
    </div>
  );
}
