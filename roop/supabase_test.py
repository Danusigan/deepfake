"""
Diagnostic tool to check Supabase storage
Run: python supabase_test.py
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BUCKET = os.getenv('SUPABASE_BUCKET', 'images')

print("=" * 70)
print("SUPABASE STORAGE DIAGNOSTIC")
print("=" * 70)

print(f"\n1. CREDENTIALS CHECK:")
print(f"   URL: {SUPABASE_URL}")
print(f"   Key: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "   Key: MISSING!")
print(f"   Bucket: {BUCKET}")

# Create client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("   ✅ Client created successfully")
except Exception as e:
    print(f"   ❌ Client creation failed: {e}")
    exit(1)

# Test 1: List files in bucket
print(f"\n2. LISTING FILES IN BUCKET '{BUCKET}':")
try:
    files = supabase.storage.from_(BUCKET).list()
    print(f"   ✅ Found {len(files)} files:")
    for f in files[:10]:  # Show first 10
        print(f"      - {f['name']} ({f.get('metadata', {}).get('size', 'unknown')} bytes)")
    if len(files) > 10:
        print(f"      ... and {len(files) - 10} more files")
except Exception as e:
    print(f"   ❌ List error: {e}")

# Test 2: Upload a test file
print(f"\n3. UPLOADING TEST FILE:")
test_content = b"TEST IMAGE DATA"
test_filename = "test_diagnostic.txt"

try:
    upload_result = supabase.storage.from_(BUCKET).upload(
        path=test_filename,
        file=test_content,
        file_options={"upsert": "true"}
    )
    print(f"   ✅ Upload successful!")
    print(f"   Response: {upload_result}")
    print(f"   Path: {upload_result.path}")
    print(f"   Full Path: {upload_result.full_path}")
except Exception as e:
    print(f"   ❌ Upload error: {e}")
    upload_result = None

# Test 3: Try different URL formats
if upload_result:
    print(f"\n4. TESTING URL FORMATS:")
    
    # Format 1: Using response.path
    url1 = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{upload_result.path}"
    print(f"\n   Format 1 (response.path):")
    print(f"   URL: {url1}")
    try:
        r = requests.get(url1, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ SUCCESS! Content: {r.content[:50]}")
        else:
            print(f"   ❌ FAILED: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")
    
    # Format 2: Using response.full_path
    url2 = f"{SUPABASE_URL}/storage/v1/object/public/{upload_result.full_path}"
    print(f"\n   Format 2 (response.full_path):")
    print(f"   URL: {url2}")
    try:
        r = requests.get(url2, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ SUCCESS! Content: {r.content[:50]}")
        else:
            print(f"   ❌ FAILED: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")
    
    # Format 3: Without bucket prefix in URL
    url3 = f"{SUPABASE_URL}/storage/v1/object/public/{test_filename}"
    print(f"\n   Format 3 (no bucket in URL):")
    print(f"   URL: {url3}")
    try:
        r = requests.get(url3, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ SUCCESS! Content: {r.content[:50]}")
        else:
            print(f"   ❌ FAILED: {r.text[:100]}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")

# Test 4: Check bucket settings
print(f"\n5. CHECKING BUCKET SETTINGS:")
try:
    # Try to get bucket info (may require admin permissions)
    buckets = supabase.storage.list_buckets()
    for b in buckets:
        if b['name'] == BUCKET:
            print(f"   ✅ Bucket found: {b}")
            print(f"   Public: {b.get('public', 'unknown')}")
            break
    else:
        print(f"   ⚠️  Bucket '{BUCKET}' not found in list")
except Exception as e:
    print(f"   ⚠️  Cannot check bucket settings: {e}")

# Test 5: Try using getPublicUrl
print(f"\n6. TESTING getPublicUrl() METHOD:")
if upload_result:
    try:
        public_url_result = supabase.storage.from_(BUCKET).get_public_url(upload_result.path)
        print(f"   ✅ getPublicUrl() returned: {public_url_result}")
        
        # Test this URL
        try:
            r = requests.get(public_url_result, timeout=5)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                print(f"   ✅ URL WORKS! Content: {r.content[:50]}")
            else:
                print(f"   ❌ URL FAILED: {r.text[:100]}")
        except Exception as e:
            print(f"   ❌ Request error: {e}")
    except Exception as e:
        print(f"   ❌ getPublicUrl() error: {e}")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
print("\n💡 NEXT STEPS:")
print("1. Check which URL format returned 200 OK")
print("2. Use that format in your supabase_utils.py")
print("3. If all URLs failed, your bucket may not be public")
print("   Go to Supabase Dashboard → Storage → images → Settings")
print("   Make sure 'Public bucket' is enabled")
print("=" * 70)