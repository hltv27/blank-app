import { NextResponse } from 'next/server';

// Free financial news via RSS-to-JSON proxy
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const topic = searchParams.get('topic') || 'finance';

  const feeds: Record<string, string> = {
    finance: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=EURUSD%3DX&region=US&lang=en-US',
    crypto:  'https://cointelegraph.com/rss',
    europe:  'https://feeds.bbci.co.uk/news/business/rss.xml',
  };

  const url = feeds[topic] || feeds.finance;

  try {
    const res = await fetch(
      `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(url)}&count=8`,
      { next: { revalidate: 900 } }
    );
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ items: [] });
  }
}
