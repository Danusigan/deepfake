"""
Quick test to see which uploaded file URLs work
"""
import requests
from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BUCKET = 'images'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Listing all files in bucket and testing their URLs...\n")

try:
    files = supabase.storage.from_(BUCKET).list()
    
    for file_obj in files[:5]:  # Test first 5 files
        filename = file_obj.get('name') or file_obj.get('id')
        
        print(f"File: {filename}")
        
        # Try different URL formats
        url1 = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"
        url2 = f"{SUPABASE_URL}/storage/v1/object/public/{filename}"
        
        # Try get_public_url
        try:
            url3 = supabase.storage.from_(BUCKET).get_public_url(filename)
            print(f"  get_public_url: {url3}")
            r = requests.head(url3, timeout=3)
            print(f"  Status: {r.status_code} {'✅' if r.status_code == 200 else '❌'}")
        except Exception as e:
            print(f"  get_public_url error: {e}")
        
        print(f"  Manual URL 1: {url1}")
        r1 = requests.head(url1, timeout=3)
        print(f"  Status: {r1.status_code} {'✅' if r1.status_code == 200 else '❌'}")
        
        print(f"  Manual URL 2: {url2}")
        r2 = requests.head(url2, timeout=3)
        print(f"  Status: {r2.status_code} {'✅' if r2.status_code == 200 else '❌'}")
        
        print()

except Exception as e:
    print(f"Error: {e}")