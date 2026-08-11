import time
import requests
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

# Target postal search zones (Replace postal codes and URLs with your target areas)
TARGET_LOCATIONS = {
    "General Area (12345)": "https://hiring.amazon.com/app#/jobSearch?query=&postal=12345&locale=en-US",
    "Location One (Area A)": "https://hiring.amazon.com/app#/jobSearch?query=&postal=11111&locale=en-US",
    "Location Two (Area B)": "https://hiring.amazon.com/app#/jobSearch?query=&postal=22222&locale=en-US",
    "Location Three (Area C)": "https://hiring.amazon.com/app#/jobSearch?query=&postal=33333&locale=en-US"
} 

# Keywords to watch for on the pages (Leave blank or add specific job titles/roles)
TARGET_TEXTS = ["Keyword One", "Keyword Two", "Keyword Three"]

NO_JOB_INDICATORS = [
    "no results", 
    "no jobs available", 
    "check back later", 
    "currently no open", 
    "no open positions"
]

def send_discord_alert(message_body):
    payload = {
        "content": message_body
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print("Discord notification sent successfully!")
        else:
            print(f"Failed to send Discord message: {response.text}")
    except Exception as e:
        print(f"Error sending Discord alert: {e}")

def scan_urls(urls_to_check):
    """Helper function to scan specific URLs and extract precise Shift Type and Duration matching portal cards."""
    matched_listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for location_name, url in urls_to_check.items():
            try:
                print(f"Scanning {location_name}...")
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                
                try:
                    page.wait_for_selector("body", timeout=5000)
                except:
                    pass
                
                page_text = page.inner_text("body")
                lower_page_text = page_text.lower()
                
                if any(phrase in lower_page_text for phrase in NO_JOB_INDICATORS):
                    print(f"-> {location_name}: Page indicates explicit 'No Jobs Available'. Skipping.")
                    time.sleep(5)
                    continue

                # STRICT CHECK: Only proceed if actual target keywords match or explicit shift card details are present.
                matched_keywords = [kw for kw in TARGET_TEXTS if kw.lower() in lower_page_text]
                
                # Precise Shift Types (Full Time, Part Time, Flex Time)
                is_full_time = "full time" in lower_page_text or "full-time" in lower_page_text
                is_part_time = "part time" in lower_page_text or "part-time" in lower_page_text
                is_flex = "flex time" in lower_page_text or "flex" in lower_page_text
                
                # Precise Durations (Regular, Seasonal)
                is_regular = "duration: regular" in lower_page_text or "regular" in lower_page_text
                is_seasonal = "duration: seasonal" in lower_page_text or "seasonal" in lower_page_text

                # Avoid false positives: If no explicit target keywords AND no concrete shift types/durations are found, skip.
                if not matched_keywords and not (is_full_time or is_part_time or is_flex or is_regular or is_seasonal):
                    print(f"-> {location_name}: No explicit keywords or shifts found. Skipping.")
                    time.sleep(5)
                    continue

                if not matched_keywords:
                    matched_keywords = ["Active Shift Card Found"]

                # Build explicit descriptions matching card elements
                type_labels = []
                if is_full_time:
                    type_labels.append("Full Time")
                if is_part_time:
                    type_labels.append("Part Time")
                if is_flex:
                    type_labels.append("Flex Time")
                
                duration_labels = []
                if is_regular:
                    duration_labels.append("Regular")
                if is_seasonal:
                    duration_labels.append("Seasonal")

                shift_type_str = ", ".join(type_labels) if type_labels else "Not Specified"
                duration_str = ", ".join(duration_labels) if duration_labels else "Not Specified"

                # Priority logic: Regular duration or Full/Part time gets priority flag
                is_priority = is_regular or is_full_time or is_part_time

                if is_regular and is_full_time:
                    badge = "🔥 [FULL TIME - REGULAR]"
                elif is_regular and is_part_time:
                    badge = "⚡ [PART TIME - REGULAR]"
                elif is_full_time:
                    badge = "🔥 [FULL TIME]"
                elif is_regular:
                    badge = "🔥 [REGULAR DURATION]"
                else:
                    badge = "📌 [JOB FOUND]"

                matched_listings.append({
                    "location": location_name,
                    "site": ", ".join(matched_keywords),
                    "badge": badge,
                    "shift_type": shift_type_str,
                    "duration": duration_str,
                    "url": url,
                    "is_priority": is_priority,
                    "is_full_time": is_full_time,
                    "is_regular": is_regular
                })
                
                time.sleep(5) # 5-second human-paced buffer between URL hops
                            
            except Exception as e:
                print(f"Error checking {location_name}: {e}")

        browser.close()
    return matched_listings

def check_for_jobs():
    print("Checking hiring pages (Precise Mapping)...")
    all_matched_listings = scan_urls(TARGET_LOCATIONS)

    if all_matched_listings:
        unique_listings = {f"{x['site']}-{x['shift_type']}-{x['duration']}-{x['location']}": x for x in all_matched_listings}.values()
        
        has_priority = any(item['is_priority'] for item in unique_listings)
        
        # Customize or remove this specific trigger check if you change your target zone name
        preferred_target_regular = any(
            item['is_regular'] and "location one" in item['location'].lower() 
            for item in unique_listings
        )

        if preferred_target_regular:
            header = "🚨🎯 **[PREFERRED TARGET REGULAR ACQUIRED] CANCEL OLD & APPLY HERE!**\n\n"
        elif has_priority:
            header = "🚨🔥 **[PRIORITY MATCH FOUND] CHECK DETAILS BELOW!**\n\n"
        else:
            header = "🚨 **[ALERT] Shift Opening Found!**\n\n"
        
        alert_msg = header
        for item in unique_listings:
            alert_msg += (
                f"**Zone:** {item['location']}\n"
                f"**Match:** {item['site']}\n"
                f"**Status:** {item['badge']}\n"
                f"**Type:** {item['shift_type']}\n"
                f"**Duration:** {item['duration']}\n"
                f"**Link:** {item['url']}\n\n"
            )
        
        if preferred_target_regular:
            alert_msg += "⚡ **ACTION REQUIRED:** Review current application status and lock down the target location!\n\n"

        print(alert_msg)
        send_discord_alert(alert_msg.strip())

        # --- 30-SECOND FOLLOW-UP VERIFICATION ---
        print("Job found! Waiting 30 seconds to re-verify if still active...")
        time.sleep(30)

        matched_locations_dict = {item['location']: item['url'] for item in unique_listings}
        recheck_listings = scan_urls(matched_locations_dict)

        if recheck_listings:
            print("Jobs still active after 30 seconds. Sending follow-up ping...")
            followup_msg = "⏰ **[FOLLOW-UP REMINDER] Shift is still up! Go lock it down!**\n\n"
            for item in recheck_listings:
                followup_msg += (
                    f"🏆 **Zone:** {item['location']}\n"
                    f"**Match:** {item['site']}\n"
                    f"**Status:** {item['badge']}\n"
                    f"**Type:** {item['shift_type']}\n"
                    f"**Duration:** {item['duration']}\n"
                    f"**Link:** {item['url']}\n\n"
                )
            send_discord_alert(followup_msg.strip())
        else:
            print("Jobs were taken or disappeared within 30 seconds. Skipping follow-up.")
    else:
        print("Checked all zones: No matching listings found.")

if __name__ == "__main__":
    print("Starting Precision Card-Mapped Job Monitor (Discord Webhook Edition)...")
    while True:
        check_for_jobs()
        time.sleep(150)
