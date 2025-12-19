"""
Test script for web scrapers.
Run this to verify scrapers work for different cities.
"""
import asyncio
from scrapers import ScraperRegistry


async def test_city(city_name: str):
    """Test scraper for a single city."""
    print(f"\n{'='*60}")
    print(f"Testing: {city_name}")
    print('='*60)
    
    try:
        # Get scraper from registry
        scraper = ScraperRegistry.get_scraper(city_name)
        print(f"✅ Using {scraper.get_platform_name()} scraper")
        print(f"📍 URL: {scraper.base_url}")
        
        # Scrape jobs with retry
        jobs = await scraper.scrape_with_retry(max_retries=2)
        
        print(f"\n✅ Successfully scraped {len(jobs)} jobs from {city_name}")
        
        # Display first 3 jobs
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n{i}. {job.title}")
            print(f"   Department: {job.department}")
            print(f"   Location: {job.location}")
            if job.salary:
                print(f"   Salary: {job.salary}")
            if job.closing_date:
                print(f"   Closes: {job.closing_date}")
            print(f"   URL: {job.url}")
        
        if len(jobs) > 3:
            print(f"\n   ... and {len(jobs) - 3} more jobs")
        
        return True, len(jobs)
        
    except Exception as e:
        print(f"❌ Error scraping {city_name}: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


async def test_all_cities():
    """Test scrapers for all configured cities."""
    supported_cities = ScraperRegistry.get_supported_cities()
    
    print(f"\n🎯 Testing {len(supported_cities)} cities")
    print(f"Cities: {', '.join(supported_cities)}")
    
    results = {}
    
    for city in supported_cities[:5]:  # Test first 5 cities
        success, job_count = await test_city(city)
        results[city] = {"success": success, "jobs": job_count}
        
        # Small delay between cities
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    for city, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {city}: {result['jobs']} jobs")
    
    successful = sum(1 for r in results.values() if r["success"])
    total_jobs = sum(r["jobs"] for r in results.values())
    
    print(f"\nSuccess Rate: {successful}/{len(results)} cities")
    print(f"Total Jobs Found: {total_jobs}")


async def test_single():
    """Quick test with a single city (Scottsdale - known NeoGov)."""
    await test_city("Scottsdale")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific city
        city_name = " ".join(sys.argv[1:])
        asyncio.run(test_city(city_name))
    else:
        # Quick single test
        print("Quick Test Mode (single city)")
        print("Run with city name to test specific city: python test_scrapers.py Phoenix")
        print("Or edit the script to run test_all_cities()\n")
        
        asyncio.run(test_single())
