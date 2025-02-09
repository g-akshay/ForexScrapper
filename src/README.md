# ...existing content...

## Setting up the Cron Job

To run the scrapers every day at 11 AM, follow these steps:

1. Open the crontab file:

   ```sh
   crontab -e
   ```

2. Add the following line to the crontab file:

   ```sh
   0 11 * * * /bin/bash /Users/akshaygundewar/Work/ForexScrapper/cron_job.sh
   ```

3. Save and exit the crontab editor.

This will schedule the `cron_job.sh` script to run every day at 11 AM.

## Installing Dependencies

Before running the scripts, make sure to install the required dependencies:

```sh
pip install -r /Users/akshaygundewar/Work/ForexScrapper/requirements.txt
```
