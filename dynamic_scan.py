import argparse
import json
import os
from browsermobproxy import Server
from selenium import webdriver

def dynamic_scan(url, output_dir, browsermob_proxy_path):
    """
    Performs a dynamic scan of a URL using Selenium and BrowserMob Proxy.

    Args:
        url (str): The URL to scan.
        output_dir (str): The directory to save the output files.
        browsermob_proxy_path (str): The path to the browsermob-proxy binary.
    """

    # Start the BrowserMob Proxy server
    server = Server(browsermob_proxy_path)
    server.start()
    proxy = server.create_proxy()

    # Configure the Selenium WebDriver to use the proxy
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"--proxy-server={proxy.proxy}")
    driver = webdriver.Chrome(options=chrome_options)

    # Start capturing network traffic
    proxy.new_har("dynamic_scan")

    # Open the URL
    driver.get(url)

    # Save the HAR file
    har_file = os.path.join(output_dir, "dynamic_scan.har")
    with open(har_file, "w") as f:
        f.write(json.dumps(proxy.har))

    # Take a screenshot
    screenshot_file = os.path.join(output_dir, "screenshot.png")
    driver.save_screenshot(screenshot_file)

    # Stop the proxy and the driver
    server.stop()
    driver.quit()

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Perform a dynamic scan of a URL.")
    parser.add_argument("url", help="The URL to scan.")
    parser.add_argument("--output-dir", default=".", help="The directory to save the output files.")
    args = parser.parse_args()

    # Get the browsermob-proxy path from the environment
    browsermob_proxy_path = os.environ.get("BROWSERMOB_PROXY_PATH")

    if not browsermob_proxy_path:
        print("Error: BROWSERMOB_PROXY_PATH environment variable is not set.")
        exit(1)

    dynamic_scan(args.url, args.output_dir, browsermob_proxy_path)