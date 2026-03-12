import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
from collections import defaultdict

import ssl

def fetch_sitemap(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return None

def parse_sitemap(xml_data):
    post_dates = defaultdict(int)
    if not xml_data:
        return post_dates

    root = ET.fromstring(xml_data)
    # The namespace in the sitemap XML
    ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    # We are looking for blog posts, typically containing '/entry/' in Tistory
    # We ignore mobile links containing '/m/entry/' to avoid duplicates
    post_url_pattern = re.compile(r'https://yongdragon9819\.tistory\.com/entry/([^/]+)$')

    for url in root.findall('sitemap:url', ns):
        loc = url.find('sitemap:loc', ns)
        lastmod = url.find('sitemap:lastmod', ns)
        
        if loc is not None and lastmod is not None:
            # Check if this URL is an actual post
            if post_url_pattern.match(loc.text):
                try:
                    # Parse Tistory's lastmod format (e.g., 2026-03-12T20:49:18+09:00 or similar)
                    date_str = lastmod.text[:10] # Get YYYY-MM-DD part
                    post_dates[date_str] += 1
                except ValueError:
                    pass
    return post_dates

def generate_svg(post_dates):
    # Calculate days for the past 365 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Grid properties
    box_size = 11
    box_margin = 3
    weeks = 53
    days_in_week = 7
    width = (weeks + 2) * (box_size + box_margin)
    height = (days_in_week + 2) * (box_size + box_margin)

    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .month {{ font-size: 10px; fill: #768390; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
        .wday {{ font-size: 9px; fill: #768390; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
    </style>
'''
    # Background
    svg_content += f'    <rect width="{width}" height="{height}" fill="#0d1117" rx="6" ry="6"/>\n'
    svg_content += f'    <g transform="translate(15, 20)">\n'

    # Color palette (GitHub Dark theme style)
    color_scheme = {
        0: "#161b22",     # No contributions
        1: "#0e4429",     # 1-2 contributions
        3: "#006d32",     # 3-4 contributions
        5: "#26a641",     # 5-6 contributions
        7: "#39d353"      # 7+ contributions
    }

    def get_color(count):
        if count == 0: return color_scheme[0]
        if count <= 2: return color_scheme[1]
        if count <= 4: return color_scheme[3]
        if count <= 6: return color_scheme[5]
        return color_scheme[7]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1
    
    # Find the starting Sunday
    # adjust start_date to be the most recent Sunday on or before start_date
    offset = (start_date.weekday() + 1) % 7 # 0=Sun, 1=Mon, ..., 6=Sat
    grid_start_date = start_date - timedelta(days=offset)

    # Weekday labels
    svg_content += f'        <text x="-14" y="24" class="wday" style="display: none;">Sun</text>\n'
    svg_content += f'        <text x="-14" y="36" class="wday">Mon</text>\n'
    svg_content += f'        <text x="-14" y="48" class="wday" style="display: none;">Tue</text>\n'
    svg_content += f'        <text x="-14" y="60" class="wday">Wed</text>\n'
    svg_content += f'        <text x="-14" y="72" class="wday" style="display: none;">Thu</text>\n'
    svg_content += f'        <text x="-14" y="84" class="wday">Fri</text>\n'
    svg_content += f'        <text x="-14" y="96" class="wday" style="display: none;">Sat</text>\n'

    current_date = grid_start_date
    
    for week in range(weeks):
        x = week * (box_size + box_margin)
        svg_content += f'        <g transform="translate({x}, 0)">\n'
        
        for day in range(days_in_week):
            # Only process up to today
            if current_date > end_date:
                break

            y = day * (box_size + box_margin)
            date_str = current_date.strftime('%Y-%m-%d')
            count = post_dates.get(date_str, 0)
            color = get_color(count)
            
            # Month labels
            if current_date.month != last_month and current_date.day <= 14:
                # Add month text above the column
                svg_content += f'            <text x="{x}" y="-8" class="month">{months[current_date.month - 1]}</text>\n'
                last_month = current_date.month

            # Draw the box
            svg_content += f'            <rect width="{box_size}" height="{box_size}" x="0" y="{y}" rx="2" ry="2" fill="{color}">\n'
            svg_content += f'                <title>{count} contributions on {date_str}</title>\n'
            svg_content += f'            </rect>\n'
            
            current_date += timedelta(days=1)
            
        svg_content += '        </g>\n'
    
    svg_content += '    </g>\n'
    
    # Legend
    legend_x = width - 110
    legend_y = height - 20
    svg_content += f'    <g transform="translate({legend_x}, {legend_y})">\n'
    svg_content += f'        <text x="-25" y="9" class="wday">Less</text>\n'
    
    for i, c in enumerate([color_scheme[0], color_scheme[1], color_scheme[3], color_scheme[5], color_scheme[7]]):
        cx = i * (box_size + box_margin)
        svg_content += f'        <rect width="{box_size}" height="{box_size}" x="{cx}" y="0" rx="2" ry="2" fill="{c}"/>\n'
        
    svg_content += f'        <text x="{5 * (box_size + box_margin) + 5}" y="9" class="wday">More</text>\n'
    svg_content += '    </g>\n'

    svg_content += '</svg>'
    
    return svg_content

if __name__ == "__main__":
    tistory_url = "https://yongdragon9819.tistory.com/sitemap.xml"
    print(f"Fetching sitemap from {tistory_url}...")
    sitemap_xml = fetch_sitemap(tistory_url)
    
    if sitemap_xml:
        print("Parsing sitemap...")
        post_dates = parse_sitemap(sitemap_xml)
        print(f"Found {sum(post_dates.values())} posts.")
        
        print("Generating SVG...")
        svg_output = generate_svg(post_dates)
        
        with open("tistory-grass.svg", "w") as f:
            f.write(svg_output)
        print("Successfully generated tistory-grass.svg")
    else:
        print("Failed to fetch or parse sitemap.")
