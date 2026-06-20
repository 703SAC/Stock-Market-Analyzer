import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Market Analyzer",
  description: "Korean stock screener, news, and LLM reports",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <nav>
          <Link href="/">홈</Link>
          <Link href="/screener">스크리너</Link>
          <Link href="/news">기사</Link>
          <Link href="/reports">보고서</Link>
          <Link href="/briefing">브리핑</Link>
          <Link href="/strategy">전략</Link>
          <Link href="/monitor">모니터</Link>
          <Link href="/context">맥락</Link>
        </nav>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
