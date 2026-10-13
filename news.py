import time
import feedparser
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

RSS_FEED = {
  "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
  "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
  "Hacker News": "https://hnrss.org/frontpage",
}

REFRESH_INTERVAL = 30 * 60 #should be 30 minutes

seen_headlines = set()

def fetch_headlines():
  headlines = []

  for source, url in RSS_FEED.items():
    feed = feedparser.parse(url)

    for entry in feed.entries[:10]:
      headline_id = entry.get("link", entry.title)

      is_new = headline_id not in seen_headlines
      seen_headlines.add(headline_id)

      headlines.append({
        "source": source,
        "title": entry.title,
        "new": is_new,
      })

  return headlines

def create_dashboard(headlines, next_refresh):
  table = Table(
    title=f"Latest News | Next Refresh: {next_refresh}",
    show_lines=True,
  )

  table.add_column("Source", style="cyan")
  table.add_column("Headline", style="white")
  table.add_column("Status", style="green")

  for item in headlines:
    table.add_row(
      item["source"],
      item["title"],
      "NEW" if item["new"] else "",
    )
  return table

def main():
  console.print("[bold green]Starting News Dashboard...[/]")

  while True:
    try:
      headlines = fetch_headlines()

      next_refresh = datetime.fromtimestamp(
        time.time() + REFRESH_INTERVAL
      ).strftime("%H:%M:%S")

      console.clear()
      console.print(
        create_dashboard(headlines, next_refresh)
      )

      time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
      console.print("\n[yellow]Dashboard stopped.[/]")
      break

    except Exception as error:
      console.print(f"[red]Error: {error}[/]")
      time.sleep(60)

if __name__ == "__main__":
  main()