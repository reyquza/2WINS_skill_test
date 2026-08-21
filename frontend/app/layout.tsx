import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "2WINS Chat",
  description: "シンプルな1対1リアルタイムチャット",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
