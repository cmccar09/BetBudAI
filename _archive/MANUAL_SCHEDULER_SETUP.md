# MANUAL TASK SCHEDULER SETUP GUIDE

Since the PowerShell script requires admin rights, here's how to set up the task manually:

## Step 1: Open Task Scheduler

1. Press `Win + R`
2. Type `taskschd.msc`
3. Press Enter

## Step 2: Create New Task

1. Click **"Create Task"** (not "Create Basic Task")
2. **General tab:**
   - Name: `RacingPostScraper`
   - Description: `Scrapes Racing Post every 30 min from 12pm-8pm`
   - Run whether user is logged on or not: ✓
   - Run with highest privileges: ✓

## Step 3: Set Up Triggers

Click **"Triggers" tab → "New"**

Create the first trigger:
- Begin the task: **On a schedule**
- Settings: **Daily**
- Start: **12:00:00 PM**
- Repeat task every: **30 minutes**
- For a duration of: **8 hours**
- Enabled: ✓
- Click OK

## Step 4: Set Up Action

Click **"Actions" tab → "New"**

- Action: **Start a program**
- Program/script: `C:\Users\charl\OneDrive\futuregenAI\Betting\run_scraper.bat`
- Start in: `C:\Users\charl\OneDrive\futuregenAI\Betting`
- Click OK

## Step 5: Configure Settings

Click **"Settings" tab:**

- ✓ Allow task to be run on demand
- ✓ Run task as soon as possible after a scheduled start is missed
- ✓ If the task fails, restart every: **1 minute** (try again: **3 times**)
- Stop the task if it runs longer than: **15 minutes**
- ✓ If the running task does not end when requested, force it to stop

## Step 6: Save

Click **OK** and enter your Windows password when prompted.

## Verify Setup

```powershell
Get-ScheduledTask -TaskName "RacingPostScraper"
```

## Test Manual Run

```powershell
Start-ScheduledTask -TaskName "RacingPostScraper"
```

Then check:
```powershell
cat scraper_log.txt
```

## Alternative: Simple Batch Loop

If Task Scheduler doesn't work, run this from 12pm-8pm:

```batch
run_scraper_loop.bat
```

It will run the scraper every 30 minutes automatically.

## Files to Use

- **Batch file**: `run_scraper.bat` (single run)
- **Python script**: `scheduled_racingpost_scraper.py` (main scraper)
- **Logs**: `scraper_log.txt` and `scraper_batch_log.txt`
