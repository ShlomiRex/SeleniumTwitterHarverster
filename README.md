# Twitter Harverster

Collects all tweets regarding a search topic. Collects the message, timestamp, sender, and even takes screenshots of the tweets.

It saves all the information in local SQLite database.

# Dependencies

1) pngquant - lossy png compression, for the screenshots. I compress the screenshots so the DB won't be huge. Add the binary to system path, to run from CMD/terminal.
2) Selenium Driver - Download of your choice: Firefox, Chrome, Safari, even Tor.