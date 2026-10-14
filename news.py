import time
import feedparser
from datetime import datetime
from rich.console import Console
from rich.table import Table
import subprocess
import threading
import select, sys, termios, tty

console = Console()

RSS_FEED = {
  "Fox News": "https://moxie.foxnews.com/google-publisher/latest.xml",
  "CNN": (
      "https://news.google.com/rss/search?"
      "q=when:24h+site:cnn.com"
      "&hl=en-US&gl=US&ceid=US:en"
  ),
  "News24": "https://feeds.capi24.com/v1/Search/articles/news24/topstories/rss",
  "Slashdot": "https://rss.slashdot.org/Slashdot/slashdotMain",
  "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
}

REFRESH_INTERVAL = 30 * 60 #should be 30 minutes

seen_headlines = set()

def fetch_headlines():
  headlines = []

  for source, url in RSS_FEED.items():
    feed = feedparser.parse(url)

    if feed.bozo:
      print(f"Warning: {source} - {feed.bozo_exception}")

    if not feed.entries:
      print(f"No headlines returned from {source}")
      continue

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
    show_lines=False,
    box=None,
    padding=(0,1),
    expand=True,
  )

  table.add_column("Source", style="cyan", width=15, no_wrap=True)
  table.add_column("Headline", style="white", overflow="ellipsis", no_wrap=True)
  table.add_column("Status", style="green", width=4)

  for item in headlines:
    table.add_row(
      item["source"],
      item["title"],
      "NEW" if item["new"] else "",
    )
  return table

def read_headlines(headlines):
  def speak():
    current_news_source = ''
    for item in headlines:    
      if item['new']:  
        new_source = item['source']
        if new_source != current_news_source:
          current_news_source = new_source
          text = f"{current_news_source}. {item['title']}"
        else:
          text = f"{item['title']}"
        subprocess.run(["say", "-r", "190", text])
  threading.Thread(target=speak, daemon=True).start()

def main():
  console.print("[bold green]Starting News Dashboard...[/]")

  old_settings = termios.tcgetattr(sys.stdin)

  try:
    tty.setcbreak(sys.stdin.fileno())

    headlines = fetch_headlines()
    next_update = time.monotonic() + REFRESH_INTERVAL

    while True:
      next_refresh = datetime.fromtimestamp(
        time.time() + max(0, next_update - time.monotonic())
      ).strftime("%H:%M:%S")

      console.clear()
      console.print(
        create_dashboard(headlines, next_refresh)
      )

      console.print(
        "\n[green]R[/] = Read Headlines | "
        "[yellow]Q[/] = Quit"
      )

      while time.monotonic() < next_update:
        if select.select([sys.stdin], [], [], 1)[0]:
          key = sys.stdin.read(1).lower()

          if key == "r":
            read_headlines(headlines)

          elif key == "q":
            return

      headlines = fetch_headlines()
      next_update = time.monotonic() + REFRESH_INTERVAL

  except KeyboardInterrupt:
    pass

  finally:
    termios.tcsetattr(
      sys.stdin,
      termios.TCSADRAIN,
      old_settings
    )
    console.print("\n[yellow]Dashboard stoppped.[/]")

if __name__ == "__main__":
  main()